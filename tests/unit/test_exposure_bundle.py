from src.domain.exposure_bundle import ExposureBundle


def test_exposure_bundle_creation():
    """
    Test création d'ExposureBundle avec valeurs par défaut
    """
    bundle = ExposureBundle()

    assert bundle.total == 0.0
    assert bundle.components == {}


def test_exposure_bundle_with_total_only():
    """
    Test création d'ExposureBundle avec seulement un total (cas Casualty/Test)
    """
    bundle = ExposureBundle(total=100_000_000)

    assert bundle.total == 100_000_000
    assert bundle.components == {}


def test_exposure_bundle_with_components():
    """
    Test création d'ExposureBundle avec composantes (cas Aviation)

    DONNÉES:
    - Total: 65,000,000
    - Hull: 15,000,000
    - Liability: 50,000,000
    """
    bundle = ExposureBundle(
        total=65_000_000,
        components={"hull": 15_000_000, "liability": 50_000_000}
    )

    assert bundle.total == 65_000_000
    assert bundle.components == {"hull": 15_000_000, "liability": 50_000_000}


def test_select_without_components():
    """
    Test select() sur un bundle sans composantes → retourne le total
    """
    bundle = ExposureBundle(total=100_000_000)

    # Sans paramètre
    assert bundle.select() == 100_000_000
    # Avec paramètre None
    assert bundle.select(None) == 100_000_000
    # Avec un set vide
    assert bundle.select(set()) == 100_000_000


def test_select_with_components_all():
    """
    Test select() avec toutes les composantes incluses
    """
    bundle = ExposureBundle(
        total=65_000_000,
        components={"hull": 15_000_000, "liability": 50_000_000}
    )

    result = bundle.select({"hull", "liability"})

    assert result == 65_000_000


def test_select_with_components_hull_only():
    """
    Test select() avec seulement Hull inclus
    """
    bundle = ExposureBundle(
        total=65_000_000,
        components={"hull": 15_000_000, "liability": 50_000_000}
    )

    result = bundle.select({"hull"})

    assert result == 15_000_000


def test_select_with_components_liability_only():
    """
    Test select() avec seulement Liability inclus
    """
    bundle = ExposureBundle(
        total=65_000_000,
        components={"hull": 15_000_000, "liability": 50_000_000}
    )

    result = bundle.select({"liability"})

    assert result == 50_000_000


def test_select_with_components_none():
    """
    Test select() avec aucun composant inclus
    """
    bundle = ExposureBundle(
        total=65_000_000,
        components={"hull": 15_000_000, "liability": 50_000_000}
    )

    result = bundle.select(set())

    assert result == 0.0


def test_fraction_to_without_components():
    """
    Test fraction_to() sur un bundle sans composantes
    """
    bundle = ExposureBundle(total=100_000_000)
    
    scaled = bundle.fraction_to(50_000_000)
    
    assert scaled.total == 50_000_000
    assert scaled.components == {}


def test_fraction_to_with_components():
    """
    Test fraction_to() sur un bundle avec composantes (mise à l'échelle proportionnelle)
    """
    bundle = ExposureBundle(
        total=100_000_000,
        components={"hull": 30_000_000, "liability": 70_000_000}
    )
    
    scaled = bundle.fraction_to(50_000_000)
    
    assert scaled.total == 50_000_000
    assert scaled.components == {"hull": 15_000_000, "liability": 35_000_000}


def test_fraction_to_with_zero_total():
    """
    Test fraction_to() quand le total original est 0
    """
    bundle = ExposureBundle(total=0.0, components={"hull": 0.0, "liability": 0.0})
    
    scaled = bundle.fraction_to(100_000_000)
    
    assert scaled.total == 100_000_000
    assert scaled.components == {}


def test_fraction_to_with_empty_components():
    """
    Test fraction_to() quand components est vide
    """
    bundle = ExposureBundle(total=100_000_000, components={})
    
    scaled = bundle.fraction_to(50_000_000)
    
    assert scaled.total == 50_000_000
    assert scaled.components == {}
