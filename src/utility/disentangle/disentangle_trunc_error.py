import numpy as np
from .. import utility
from ..riemannian_optimization import conjugate_gradients
from ..riemannian_optimization import trust_region_method
from ..riemannian_optimization import stiefel_manifold
from . import truncErrorIterate
from .. import debug_levels

def disentangle_CG(theta, chi, debug_dict=None, **kwargs):
    """
    Disentangles the given wavefunction theta by minimizing the truncation error, using Conjugate Gradients.
    The disentangling unitary is initialized with identity.

    Parameters
    ----------
    theta : np.ndarray of shape (l, i, j, r)
        wavefunction tensor to be disentangled.
    chi : int
        truncated bond dimension used for the computation of the cost function
    debug_dict : dictionary, optional
        dictionary in which debug information is saved. Default: None.
    **kwargs
        remaining kwargs are passed into the initialization of conjugate_gradients.ConjugateGradientsOptimizer()
        see src/utility/riemannian_optimization/conjugate_gradients.py for more information.
        
    Returns
    -------
    U_final : np.ndarray of shape (i, j, i*, j*)
        final disentangling unitary after optimization
    """
    # Initialize disentangling unitary with identity
    _, D1, D2, _ = theta.shape
    U0 = np.reshape(np.eye(D1*D2).astype(np.complex128), (D1, D2, D1, D2))
    # Perform TRM optimization
    construct_new_iterate = lambda U, _ : truncErrorIterate.TruncErrorIterateCG(U, theta, chi, chi_max=None, N_iters_svd=None, eps_svd=0, old_iterate=None)
    manifold = stiefel_manifold.ComplexStiefelManifold(n=D1*D2, p=D1*D2, shape=U0.shape)
    conjugateGradientsOptimizer = conjugate_gradients.ConjugateGradientsOptimizer(manifold=manifold, construct_iterate=construct_new_iterate, **kwargs)
    log_debug_info = debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_PER_ITERATION_DEBUG_INFO_DISENTANGLER_TRIPARTITE_DECOMPOSITION)
    iterate, n, num_restarts_not_descent, num_restarts_powell, debug_info = conjugateGradientsOptimizer.optimize(construct_new_iterate(U0, None), log_debug_info=log_debug_info)
    if debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_DISENTANGLER_TRIPARTITE_DECOMPOSITION_ITERATION_INFO):
        utility.append_to_dict_list(debug_dict, "N_iters_disentangler", n)
        utility.append_to_dict_list(debug_dict, "disentangler_num_restarts_not_descent", num_restarts_not_descent)
        utility.append_to_dict_list(debug_dict, "disentangler_num_restarts_powell", num_restarts_powell)
    if log_debug_info:
        debug_dict["disentangler_iterates"] = debug_info[0]
        debug_dict["disentangler_costs"] = debug_info[1]
        debug_dict["disentangler_step_sizes"] = debug_info[2]
    return iterate

def disentangle_approx_CG(theta, chi, N_iters_svd=5, eps_svd=0.0, N_iters_svd_initial=50, debug_dict=None, **kwargs):
    """
    Disentangles the given wavefunction theta by minimizing the truncation error, using Conjugate Gradients 
    with an approximate cost function. The disentangling unitary is initialized with identity.

    Parameters
    ----------
    theta : np.ndarray of shape (l, i, j, r)
        wavefunction tensor to be disentangled.
    chi : int
        truncated bond dimension used for the computation of the cost function
    N_iters_svd : int or None, optional
        number of iterations the qr splitting algorithm is run for approximating the SVD.
        If this is set to None, a full SVD is performed instead. Default: 5.
    eps_svd : float, optional 
        eps parameter passed into split_matrix_iterate_QR(), 
        see src/utility/utility.py for more information. Default: 0.0.
    N_iters_svd_initial : int or None, optional
        number of iterations the qr splitting algorithm is run for the initial iterate.
        Generally should be equal or larger than N_iters_svd. Default: 5.
    debug_dict : dictionary, optional
        dictionary in which debug information is saved. Default: None.
    **kwargs
        remaining kwargs are passed into the initialization of conjugate_gradients.ConjugateGradientsOptimizer()
        see src/utility/riemannian_optimization/conjugate_gradients.py for more information.
        
    Returns
    -------
    U_final : np.ndarray of shape (i, j, i*, j*)
        final disentangling unitary after optimization
    """
    # Initialize disentangling unitary with identity
    _, D1, D2, _ = theta.shape
    U0 = np.reshape(np.eye(D1*D2).astype(np.complex128), (D1, D2, D1, D2))
    # Perform TRM optimization
    construct_new_iterate = lambda U, old_iterate : truncErrorIterate.TruncErrorIterateCG(U, theta, chi, chi_max=None, N_iters_svd=N_iters_svd, eps_svd=eps_svd)
    manifold = stiefel_manifold.ComplexStiefelManifold(n=D1*D2, p=D1*D2, shape=U0.shape)
    conjugateGradientsOptimizer = conjugate_gradients.ConjugateGradientsOptimizer(manifold=manifold, construct_iterate=construct_new_iterate, **kwargs)
    log_debug_info = debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_PER_ITERATION_DEBUG_INFO_DISENTANGLER_TRIPARTITE_DECOMPOSITION)
    iterate, n, num_restarts_not_descent, num_restarts_powell, debug_info = conjugateGradientsOptimizer.optimize(truncErrorIterate.TruncErrorIterateCG(U0, theta, chi, chi_max=None, N_iters_svd=N_iters_svd_initial, eps_svd=eps_svd, old_iterate=None), log_debug_info=log_debug_info)
    if debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_DISENTANGLER_TRIPARTITE_DECOMPOSITION_ITERATION_INFO):
        utility.append_to_dict_list(debug_dict, "N_iters_disentangler", n)
        utility.append_to_dict_list(debug_dict, "disentangler_num_restarts_not_descent", num_restarts_not_descent)
        utility.append_to_dict_list(debug_dict, "disentangler_num_restarts_powell", num_restarts_powell)
    if log_debug_info:
        debug_dict["disentangler_iterates"] = debug_info[0]
        debug_dict["disentangler_costs"] = debug_info[1]
        debug_dict["disentangler_step_sizes"] = debug_info[2]
    return iterate

def disentangle_TRM(theta, chi, debug_dict=None, **kwargs):
    """
    Disentangles the given wavefunction theta by minimizing the renyi-entropy, using the Trust Region method.
    The disentangling unitary is initialized with identity.

    Parameters
    ----------
    theta : np.ndarray of shape (l, i, j, r)
        wavefunction tensor to be disentangled.
    chi : int
        truncated bond dimension used for the computation of the cost function
    debug_dict : dictionary, optional
        dictionary in which debug information is saved. Default: None.
    **kwargs
        remaining kwargs are passed into the initialization of trust_region_method.TrustRegionOptimizer()
        see src/utility/riemannian_optimization/trust_region_method.py for more information.
        
    Returns
    -------
    U_final : np.ndarray of shape (i, j, i*, j*)
        final disentangling unitary after optimization
    """
    # Initialize disentangling unitary with identity
    _, D1, D2, _ = theta.shape
    U0 = np.reshape(np.eye(D1*D2).astype(np.complex128), (D1, D2, D1, D2))
    # Perform TRM optimization
    construct_new_iterate = lambda U, _ : truncErrorIterate.TruncErrorIterateTRM(U, theta, chi)
    manifold = stiefel_manifold.ComplexStiefelManifold(n=D1*D2, p=D1*D2, shape=U0.shape)
    trustRegionOptimizer = trust_region_method.TrustRegionOptimizer(manifold, construct_new_iterate, **kwargs)
    log_debug_info = debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_PER_ITERATION_DEBUG_INFO_DISENTANGLER_TRIPARTITE_DECOMPOSITION)
    iterate, n, debug_info = trustRegionOptimizer.optimize(construct_new_iterate(U0, None), log_debug_info=log_debug_info, print_warnings=False)
    if debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_DISENTANGLER_TRIPARTITE_DECOMPOSITION_ITERATION_INFO):
        utility.append_to_dict_list(debug_dict, "N_iters_disentangler", n)
    if log_debug_info:
        debug_dict["disentangler_iterates"] = debug_info[0]
        debug_dict["disentangler_costs"] = debug_info[1]
        debug_dict["disentangler_deltas"] = debug_info[2]
        debug_dict["disentangler_tCG_iters"] = debug_info[3]
    return iterate

def disentangle_approx_TRM(theta, chi, chi_max=None, N_iters_svd=2, eps_svd=0.0, N_iters_svd_initial=50, debug_dict=None, **kwargs):
    """
    Disentangles the given wavefunction theta by minimizing the renyi-entropy, using the Trust Region method
    with an approximate cost function. The disentangling unitary is initialized with identity.

    Parameters
    ----------
    theta : np.ndarray of shape (l, i, j, r)
        wavefunction tensor to be disentangled.
    chi : int
        truncated bond dimension used for the computation of the cost function
    chi_max : int or None, optional
        bond dimension that is used to approximate the computation of the hessian.
        lower chi_max leads to a worse approximation but to a faster algorithm.
        If chi_max is None, it is set to chi. Default: None.
    renyi_alpha : float, optional
        renyi alpha. Default: 0.5.
    N_iters_svd : int or None, optional
        number of iterations the qr splitting algorithm is run for approximating the SVD.
        If this is set to None, a full SVD is performed instead. Default: 2.
    eps_svd : float, optional 
        eps parameter passed into split_matrix_iterate_QR(), 
        see src/utility/utility.py for more information. Default: 0.0.
    N_iters_svd_initial : int or None, optional
        number of iterations the qr splitting algorithm is run for the initial iterate.
        Generally should be equal or larger than N_iters_svd. Default: 2.
    debug_dict : dictionary, optional
        dictionary in which debug information is saved. Default: None.
    **kwargs
        remaining kwargs are passed into the initialization of trust_region_method.TrustRegionOptimizer()
        see src/utility/riemannian_optimization/trust_region_method.py for more information.
        
    Returns
    -------
    U_final : np.ndarray of shape (i, j, i*, j*)
        final disentangling unitary after optimization
    """
    if chi_max is None:
        chi_max = chi
    # Initialize disentangling unitary with identity
    _, D1, D2, _ = theta.shape
    U0 = np.reshape(np.eye(D1*D2).astype(np.complex128), (D1, D2, D1, D2))
    # Perform TRM optimization
    construct_new_iterate = lambda U, old_iterate : truncErrorIterate.TruncErrorIterateApproxTRM(U, theta, chi, chi_max=chi_max, N_iters_svd=N_iters_svd, eps_svd=eps_svd, old_iterate=old_iterate)
    manifold = stiefel_manifold.ComplexStiefelManifold(n=D1*D2, p=D1*D2, shape=U0.shape)
    trustRegionOptimizer = trust_region_method.TrustRegionOptimizer(manifold, construct_new_iterate, **kwargs)
    log_debug_info = debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_PER_ITERATION_DEBUG_INFO_DISENTANGLER_TRIPARTITE_DECOMPOSITION)
    iterate, n, debug_info = trustRegionOptimizer.optimize(truncErrorIterate.TruncErrorIterateApproxTRM(U0, theta, chi, chi_max=chi_max, N_iters_svd=N_iters_svd_initial, eps_svd=eps_svd, old_iterate=None), log_debug_info=log_debug_info, print_warnings=False)
    if debug_levels.check_debug_level(debug_dict, debug_levels.DebugLevel.LOG_DISENTANGLER_TRIPARTITE_DECOMPOSITION_ITERATION_INFO):
        utility.append_to_dict_list(debug_dict, "N_iters_disentangler", n)
    if log_debug_info:
        debug_dict["disentangler_iterates"] = debug_info[0]
        debug_dict["disentangler_costs"] = debug_info[1]
        debug_dict["disentangler_deltas"] = debug_info[2]
        debug_dict["disentangler_tCG_iters"] = debug_info[3]
    return iterate

def disentangle(theta, chi, method="trm", debug_dict=None, **kwargs):
    """
    Disentangles the given wavefunction theta by minimizing the truncation error.

    Parameters
    ----------
    theta : np.ndarray of shape (l, i, j, r)
        wavefunction tensor to be disentangled.
    chi : int
        truncated bond dimension used for the computation of the cost function
    method : str, one of {"trm", "cg"}, optional
        method used to minimize the entropy.
    debug_dict : dictionary, optional
        dictionary in which debug information is saved. Default: None.
    **kwargs
        remaining kwargs are passed into the respective method chosen with method.
        See the different called functions for more information.

    Returns
    -------
    U_final : np.ndarray of shape (i, j, i*, j*)
        final disentangling unitary after optimization
    """
    if method == "trm":
        return disentangle_TRM(theta, chi=chi, debug_dict=debug_dict, **kwargs)
    elif method == "cg":    
        return disentangle_CG(theta, chi=chi, debug_dict=debug_dict, **kwargs)
    else:
        raise NotImplementedError(f"disentangling method \"{method}\" is not implemented for truncation error disentangling!")

def disentangle_approx(theta, chi, method="cg", debug_dict=None, **kwargs):
    """
    Disentangles the given wavefunction theta by minimizing an approximation of the truncation error.

    Parameters
    ----------
    theta : np.ndarray of shape (l, i, j, r)
        wavefunction tensor to be disentangled.
    chi : int
        bond dimension that the SVD of Utheta is truncated to. Smaller chi will speed up the algorithm
        but generally lead to worse results.
    method : str, one of {"trm", "cg"}, optional
        method used to minimize the entropy.
    debug_dict : dictionary, optional
        dictionary in which debug information is saved. Default: None.
    **kwargs
        remaining kwargs are passed into the respective method chosen with method.
        See the different called functions for more information.

    RReturns
    -------
    U_final : np.ndarray of shape (i, j, i*, j*)
        final disentangling unitary after optimization
    """
    if method == "trm":
        return disentangle_approx_TRM(theta, chi, debug_dict=debug_dict, **kwargs)
    elif method == "cg":    
        return disentangle_approx_CG(theta, chi, debug_dict=debug_dict, **kwargs)
    else:
        raise NotImplementedError(f"disentangling method \"{method}\" is not implemented for approximate truncation error disentangling!")