from __future__ import print_function

import numpy as np

from tractor import PointSource, getParamTypeTree, RaDecPos
from tractor.galaxy import ExpGalaxy, DevGalaxy
from tractor.sersic import SersicGalaxy, SersicIndex
from tractor.ellipses import EllipseESoft, EllipseE
from legacypipe.survey import RexGalaxy, GaiaSource

# FITS catalogs

fits_reverse_typemap = { 'PSF': PointSource,
                         'EXP': ExpGalaxy,
                         'DEV': DevGalaxy,
                         'SER': SersicGalaxy,
                         'REX': RexGalaxy,
                         'NUN': type(None),
                         'DUP': GaiaSource,
                         }

fits_typemap = dict([(v,k) for k,v in fits_reverse_typemap.items()])
fits_typemap[GaiaSource] = 'PSF'

fits_short_typemap = { PointSource:  'P',
                       ExpGalaxy:    'E',
                       DevGalaxy:    'D',
                       SersicGalaxy: 'S',
                       RexGalaxy:    'R',
                       GaiaSource:   'G' }

def _typestring(t):
    return '%s.%s' % (t.__module__, t.__name__)

def _get_ellipse_types():
    return [EllipseE, EllipseESoft]

def _source_param_types(src):
    def flatten_node(node):
        from functools import reduce
        return reduce(lambda x,y: x+y,
                      [flatten_node(c) for c in node[1:]],
                      [node[0]])
    tree = getParamTypeTree(src)
    #print('Source param types:', tree)
    types = flatten_node(tree)
    return types

def prepare_fits_catalog(cat, invvars, T, hdr, bands, allbands=None,
                         prefix='', save_invvars=True):
    if T is None:
        from astrometry.util.fits import fits_table
        T = fits_table()
    if hdr is None:
        import fitsio
        hdr = fitsio.FITSHDR()
    if allbands is None:
        allbands = bands

    hdr.add_record(dict(name='TR_VER', value=1, comment='Tractor output format version'))

    # Find a source of each type and query its parameter names, for the header.
    # ASSUMES the catalog contains at least one object of each type
    for t,ts in fits_short_typemap.items():
        for src in cat:
            if type(src) != t:
                continue
            #print('Parameters for', t, src)
            sc = src.copy()
            sc.thawAllRecursive()
            for i,nm in enumerate(sc.getParamNames()):
                hdr.add_record(dict(name='TR_%s_P%i' % (ts, i), value=nm,
                                    comment='Tractor param name'))

            for i,t in enumerate(_source_param_types(sc)):
                t = _typestring(t)
                hdr.add_record(dict(name='TR_%s_T%i' % (ts, i),
                                    value=t, comment='Tractor param type'))
            break

    params0 = cat.getParams()

    flux = np.zeros((len(cat), len(allbands)), np.float32)
    flux_ivar = np.zeros((len(cat), len(allbands)), np.float32)

    for band in bands:
        i = allbands.index(band)
        for j,src in enumerate(cat):
            if src is not None:
                flux[j,i] = sum(b.getFlux(band) for b in src.getBrightnesses())

        if invvars is None:
            continue
        # Oh my, this is tricky... set parameter values to the variance
        # vector so that we can read off the parameter variances via the
        # python object apis.
        cat.setParams(invvars)

        for j,src in enumerate(cat):
            if src is not None:
                flux_ivar[j,i] = sum(b.getFlux(band) for b in src.getBrightnesses())

        cat.setParams(params0)

    T.set('%sflux' % prefix, flux)
    if save_invvars:
        T.set('%sflux_ivar' % prefix, flux_ivar)

    _get_tractor_fits_values(T, cat, '%s%%s' % prefix)

    if save_invvars:
        if invvars is not None:
            cat.setParams(invvars)
        else:
            cat.setParams(np.zeros(cat.numberOfParams()))
        _get_tractor_fits_values(T, cat, '%s%%s_ivar' % prefix)
        # Heh, "no uncertainty here!"
        T.delete_column('%stype_ivar' % prefix)
    cat.setParams(params0)

    # mod RA
    ra = T.get('%sra' % prefix)
    ra += (ra <   0) * 360.
    ra -= (ra > 360) * 360.

    # Downconvert RA,Dec invvars to float32
    for c in ['ra','dec']:
        col = '%s%s_ivar' % (prefix, c)
        T.set(col, T.get(col).astype(np.float32))

    # Zero out unconstrained values
    flux = T.get('%s%s' % (prefix, 'flux'))
    iv = T.get('%s%s' % (prefix, 'flux_ivar'))
    flux[iv == 0] = 0.

    return T, hdr

def _get_tractor_fits_values(T, cat, pat):
    typearray = np.array([fits_typemap[type(src)] for src in cat])
    typearray = typearray.astype('S3')
    T.set(pat % 'type', typearray)

    ra,dec = [],[]
    for src in cat:
        if src is None:
            ra.append(0.)
            dec.append(0.)
        else:
            pos = src.getPosition()
            ra.append(pos.ra)
            dec.append(pos.dec)
    T.set(pat % 'ra',  np.array(ra))
    T.set(pat % 'dec', np.array(dec))

    shape = np.zeros((len(T), 3), np.float32)
    # sersic index
    sersic = np.zeros(len(T), np.float32)

    for i,src in enumerate(cat):
        if isinstance(src, RexGalaxy):
            shape[i,0] = src.shape.getAllParams()[0]
        elif isinstance(src, (ExpGalaxy, DevGalaxy, SersicGalaxy)):
            shape[i,:] = src.shape.getAllParams()

        if isinstance(src, SersicGalaxy):
            sersic[i] = src.sersicindex.getValue()

    T.set(pat % 'sersic',  sersic)

    T.set(pat % 'shape_r',  shape[:,0])
    T.set(pat % 'shape_e1', shape[:,1])
    T.set(pat % 'shape_e2', shape[:,2])

def read_fits_catalog(T, hdr=None, invvars=False, bands='grz',
                      allbands=None, ellipseClass=EllipseE,
                      fluxPrefix=''):
    '''
    This is currently a weird hybrid of dynamic and hard-coded.

    Return list of tractor Sources.

    If invvars=True, return sources,invvars
    where invvars is a list matching sources.getParams()

    If *ellipseClass* is set, assume that type for galaxy shapes; if None,
    read the type from the header.
    '''
    from tractor import NanoMaggies
    if hdr is None:
        hdr = T._header
    if allbands is None:
        allbands = bands
    rev_typemap = fits_reverse_typemap

    T.shape = np.vstack((T.shape_r, T.shape_e1, T.shape_e2)).T

    ibands = np.array([allbands.index(b) for b in bands])

    ellipse_types = dict([(_typestring(t), t) for t in
                          _get_ellipse_types()])
    ivs = []
    cat = []
    for t in T:
        typestr = t.type.strip()
        # # Gaia -- check REF_CAT = 'G2'
        # if t.ref_cat == 'G2' and typestr == 'PSF':
        #     clazz = GaiaSource
        clazz = rev_typemap[typestr]
        pos = RaDecPos(t.ra, t.dec)
        assert(np.isfinite(t.ra))
        assert(np.isfinite(t.dec))

        shorttype = fits_short_typemap[clazz]

        if fluxPrefix + 'flux' in t.get_columns():
            flux = np.atleast_1d(t.get(fluxPrefix + 'flux'))
            assert(np.all(np.isfinite(flux[ibands])))
            br = NanoMaggies(order=bands,
                             **dict(zip(bands, flux[ibands])))
        else:
            fluxes = {}
            for b in bands:
                fluxes[b] = t.get(fluxPrefix + 'flux_' + b)
                assert(np.all(np.isfinite(fluxes[b])))
            br = NanoMaggies(order=bands, **fluxes)

        params = [pos, br]
        if invvars:
            # ASSUME & hard-code that the position and brightness are
            # the first params

            if fluxPrefix + 'flux_ivar' in t.get_columns():
                fluxiv = np.atleast_1d(t.get(fluxPrefix + 'flux_ivar'))
                fluxivs = list(fluxiv[ibands])
            else:
                fluxivs = []
                for b in bands:
                    fluxivs.append(t.get(fluxPrefix + 'flux_ivar_' + b))
            ivs.extend([t.ra_ivar, t.dec_ivar] + fluxivs)

        if issubclass(clazz, (DevGalaxy, ExpGalaxy, SersicGalaxy)):
            if ellipseClass is not None:
                eclazz = ellipseClass
            else:
                # hard-code knowledge that third param is the ellipse
                eclazz = hdr['TR_%s_T3' % shorttype]
                # drop any double-quoted weirdness
                eclazz = eclazz.replace('"','')
                # look up that string... to avoid eval()
                eclazz = ellipse_types[eclazz]

            assert(np.all([np.isfinite(x) for x in t.shape]))
            ell = eclazz(*t.shape)
            params.append(ell)
            if invvars:
                ivs.extend(t.shape_ivar)

        elif issubclass(clazz, PointSource):
            pass
        else:
            raise RuntimeError('Unknown class %s' % str(clazz))

        from legacypipe.survey import LegacySersicIndex
        sersic_index_types = dict([(_typestring(t), t) for t in
                                   [SersicIndex, LegacySersicIndex]])

        if issubclass(clazz, SersicGalaxy):
            # hard-code knowledge that fourth param is the Sersic index
            iclazz = hdr['TR_%s_T4' % shorttype]
            iclazz = iclazz.replace('"','')
            # look up that string... to avoid eval()
            iclazz = sersic_index_types[iclazz]
            si = iclazz(t.sersic)
            params.append(si)
            if invvars:
                ivs.append(t.sersic_ivar)

        src = clazz(*params)
        cat.append(src)

    if invvars:
        ivs = np.array(ivs)
        ivs[np.logical_not(np.isfinite(ivs))] = 0
        return cat, ivs
    return cat
