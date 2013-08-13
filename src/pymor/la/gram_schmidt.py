# This file is part of the pyMor project (http://www.pymor.org).
# Copyright Holders: Felix Albrecht, Rene Milk, Stephan Rave
# License: BSD 2-Clause License (http://opensource.org/licenses/BSD-2-Clause)
#
# Contributors: Andreas Buhr

from __future__ import absolute_import, division, print_function

import numpy as np

from pymor import defaults
from pymor.core import getLogger
from pymor.core.exceptions import AccuracyError
from pymor.tools import float_cmp_all


def gram_schmidt(A, product=None, tol=None, offset=0, find_duplicates=None,
                 reiterate=None, reiteration_threshold=None, check=None, check_tol=None):
    '''Orthonormnalize a matrix using the Gram-Schmidt algorithm.

    Parameters
    ----------
    A
        The VectorArray which is to be orthonormalized.
    product
        The scalar product w.r.t. which to orthonormalize.
    tol
        Tolerance to determine a linear dependent row.
    offset
        Assume that the first `offset` vectors are already orthogonal and start the
        algorithm at the `offset + 1`-th vector.
    find_duplicates
        If `True`, eliminate duplicate vectors before the main loop.
    reiterate:
        If `True`, orthonormalize again if the norm of the orthogonalized vector is
        much smaller than the norm of the original vector.
    reiteration_threshold:
        If `reiterate` is `True`, reorthonormalize if the ratio between the norms of
        the orthogonalized vector and the original vector is smaller than this value.
    check
        If `True`, check if the resulting VectorArray is really orthonormal. If `None`, use
        `defaults.gram_schmidt_check`.
    check_tol
        Tolerance for the check. If `None`, `defaults.gram_schmidt_check_tol` is used.


    Returns
    -------
    The orthonormalized matrix.
    '''

    logger = getLogger('pymor.la.gram_schmidt.gram_schmidt')
    tol = defaults.gram_schmidt_tol if tol is None else tol
    find_duplicates = defaults.gram_schmidt_find_duplicates if find_duplicates is None else find_duplicates
    reiterate = defaults.gram_schmidt_reiterate if reiterate is None else reiterate
    reiteration_threshold = defaults.gram_schmidt_reiteration_threshold if reiteration_threshold is None \
        else reiteration_threshold
    check = defaults.gram_schmidt_tol if check is None else check
    check_tol = check_tol or defaults.gram_schmidt_check_tol

    # find duplicate vectors since in some circumstances these cannot be detected in the main loop
    # (is this really needed or is in this cases the tolerance poorly chosen anyhow)
    if find_duplicates:
        for i in xrange(len(A)):
            duplicates = A.almost_equal(A, ind=i, o_ind=np.arange(max(offset, i + 1), len(A)))
            if np.any(duplicates):
                A.remove(np.where(duplicates))
                logger.info("Removing duplicate vectors")

    # main loop
    remove = []
    for i in xrange(offset, len(A)):
        # first calculate norm
        if product is None:
            oldnorm = A.l2_norm(ind=i)[0]
        else:
            oldnorm = np.sqrt(product.apply2(A, A, V_ind=i, U_ind=i, pairwise=True))[0]

        if i == 0:
            A.scal(1/oldnorm, ind=0)

        else:
            first_iteration = True

            # If reiterate is True, reiterate as long as the norm of the vector decreases
            # strongly during orthogonalization (due to Andreas Buhr).
            while first_iteration or reiterate and norm / oldnorm < reiteration_threshold:
                # this loop assumes that oldnorm is the norm of the ith vector when entering

                if first_iteration:
                    first_iteration = False
                else:
                    logger.info('Orthonormalizing vector {} again'.format(i))

                # orthogonalize to all vectors left
                for j in xrange(i):
                    if j in remove:
                        continue
                    if product is None:
                        p = A.dot(A, ind=i, o_ind=j, pairwise=True)[0]
                    else:
                        p = product.apply2(A, A, V_ind=i, U_ind=j, pairwise=True)[0]
                    A.axpy(-p, A, ind=i, x_ind=j)

                # calculate new norm
                if product is None:
                    norm = A.l2_norm(ind=i)[0]
                else:
                    norm = np.sqrt(product.apply2(A, A, V_ind=i, U_ind=i, pairwise=True))[0]

                # remove vector if it got too small:
                if norm / oldnorm < tol:
                    logger.info("Removing linear dependent vector {}".format(i))
                    remove.append(i)
                    break

                A.scal(1 / norm, ind=i)
                oldnorm = 1.

    if remove:
        A.remove(remove)

    if check:
        if not product and not float_cmp_all(A.dot(A, pairwise=False), np.eye(len(A)), check_tol):
            err = np.max(np.abs(A.dot(A, pairwise=False) - np.eye(len(A))))
            raise AccuracyError('result not orthogonal (max err={})'.format(err))
        elif product and not float_cmp_all(product.apply2(A, A, pairwise=False), np.eye(len(A)), check_tol):
            err = np.max(np.abs(product.apply2(A, A, pairwise=False) - np.eye(len(A))))
            raise AccuracyError('result not orthogonal (max err={})'.format(err))

    return A
