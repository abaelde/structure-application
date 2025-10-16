from src.domain.policy import Policy
from src.domain.exposure_bundle import ExposureBundle


def test_policy_exposure_bundle_aviation():
    """
    Test exposure_bundle() pour l'aviation avec composantes Hull/Liability
    """
    policy_data = {
        "HULL_LIMIT": 100_000_000,
        "LIABILITY_LIMIT": 500_000_000,
        "HULL_SHARE": 0.15,
        "LIABILITY_SHARE": 0.10,
    }
    
    policy = Policy(raw=policy_data, uw_dept="aviation")
    
    bundle = policy.exposure_bundle("aviation")
    
    assert isinstance(bundle, ExposureBundle)
    assert bundle.total == 65_000_000  # 15M + 50M
    assert bundle.components["hull"] == 15_000_000
    assert bundle.components["liability"] == 50_000_000


def test_policy_exposure_bundle_casualty():
    """
    Test exposure_bundle() pour casualty (pas de composantes)
    """
    policy_data = {
        "LIMIT": 100_000_000,
        "CEDENT_SHARE": 0.5,
    }
    
    policy = Policy(raw=policy_data, uw_dept="casualty")
    
    bundle = policy.exposure_bundle("casualty")
    
    assert isinstance(bundle, ExposureBundle)
    assert bundle.total == 50_000_000  # 100M * 0.5
    assert bundle.components == {}  # Pas de composantes pour casualty


def test_policy_exposure_bundle_test():
    """
    Test exposure_bundle() pour test (pas de composantes)
    """
    policy_data = {
        "exposure": 75_000_000,
    }
    
    policy = Policy(raw=policy_data, uw_dept="test")
    
    bundle = policy.exposure_bundle("test")
    
    assert isinstance(bundle, ExposureBundle)
    assert bundle.total == 75_000_000
    assert bundle.components == {}  # Pas de composantes pour test


def test_policy_exposure_bundle_caching():
    """
    Test que exposure_bundle() utilise le cache
    """
    policy_data = {
        "HULL_LIMIT": 100_000_000,
        "LIABILITY_LIMIT": 500_000_000,
        "HULL_SHARE": 0.15,
        "LIABILITY_SHARE": 0.10,
    }
    
    policy = Policy(raw=policy_data, uw_dept="aviation")
    
    # Premier appel
    bundle1 = policy.exposure_bundle("aviation")
    
    # Deuxième appel (devrait utiliser le cache)
    bundle2 = policy.exposure_bundle("aviation")
    
    # Même objet (cache)
    assert bundle1 is bundle2
    assert bundle1.total == 65_000_000
