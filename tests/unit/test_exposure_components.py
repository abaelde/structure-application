from src.engine import ExposureComponents


def test_exposure_components_creation():
    """
    Test création d'ExposureComponents avec valeurs par défaut
    """
    components = ExposureComponents()

    assert components.hull == 0.0
    assert components.liability == 0.0
    assert components.total == 0.0


def test_exposure_components_with_values():
    """
    Test création d'ExposureComponents avec des valeurs

    DONNÉES:
    - Hull: 15,000,000
    - Liability: 50,000,000

    ATTENDU:
    - Total: 65,000,000
    """
    components = ExposureComponents(hull=15_000_000, liability=50_000_000)

    assert components.hull == 15_000_000
    assert components.liability == 50_000_000
    assert components.total == 65_000_000


def test_apply_filters_both_included():
    """
    Test apply_filters avec Hull et Liability inclus

    DONNÉES:
    - Hull: 15,000,000
    - Liability: 50,000,000
    - Filtres: Hull=True, Liability=True

    ATTENDU:
    - Résultat: 65,000,000 (tout inclus)
    """
    components = ExposureComponents(hull=15_000_000, liability=50_000_000)

    result = components.apply_filters(includes_hull=True, includes_liability=True)

    assert result == 65_000_000


def test_apply_filters_hull_only():
    """
    Test apply_filters avec seulement Hull inclus

    DONNÉES:
    - Hull: 15,000,000
    - Liability: 50,000,000
    - Filtres: Hull=True, Liability=False

    ATTENDU:
    - Résultat: 15,000,000 (seulement Hull)
    """
    components = ExposureComponents(hull=15_000_000, liability=50_000_000)

    result = components.apply_filters(includes_hull=True, includes_liability=False)

    assert result == 15_000_000


def test_apply_filters_liability_only():
    """
    Test apply_filters avec seulement Liability inclus

    DONNÉES:
    - Hull: 15,000,000
    - Liability: 50,000,000
    - Filtres: Hull=False, Liability=True

    ATTENDU:
    - Résultat: 50,000,000 (seulement Liability)
    """
    components = ExposureComponents(hull=15_000_000, liability=50_000_000)

    result = components.apply_filters(includes_hull=False, includes_liability=True)

    assert result == 50_000_000


def test_apply_filters_none_included():
    """
    Test apply_filters avec aucun composant inclus

    DONNÉES:
    - Hull: 15,000,000
    - Liability: 50,000,000
    - Filtres: Hull=False, Liability=False

    ATTENDU:
    - Résultat: 0 (rien inclus)

    Note: Ce cas ne devrait pas se produire dans la pratique car la validation
    du modèle condition empêche d'avoir les deux à False, mais on teste quand même
    la méthode apply_filters de manière isolée.
    """
    components = ExposureComponents(hull=15_000_000, liability=50_000_000)

    result = components.apply_filters(includes_hull=False, includes_liability=False)

    assert result == 0.0


def test_apply_filters_with_zero_hull():
    """
    Test apply_filters quand Hull est à 0

    DONNÉES:
    - Hull: 0
    - Liability: 50,000,000
    - Filtres: Hull=True, Liability=True

    ATTENDU:
    - Résultat: 50,000,000
    """
    components = ExposureComponents(hull=0, liability=50_000_000)

    result = components.apply_filters(includes_hull=True, includes_liability=True)

    assert result == 50_000_000


def test_apply_filters_with_zero_liability():
    """
    Test apply_filters quand Liability est à 0

    DONNÉES:
    - Hull: 15,000,000
    - Liability: 0
    - Filtres: Hull=True, Liability=True

    ATTENDU:
    - Résultat: 15,000,000
    """
    components = ExposureComponents(hull=15_000_000, liability=0)

    result = components.apply_filters(includes_hull=True, includes_liability=True)

    assert result == 15_000_000
