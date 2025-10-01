def quote_part(exposition: float, taux_cession: float) -> float:
    if not 0 <= taux_cession <= 1:
        raise ValueError("Le taux de cession doit être entre 0 et 1")
    
    return exposition * taux_cession


def excess_of_loss(exposition: float, priorite: float, portee: float) -> float:
    if priorite < 0 or portee < 0:
        raise ValueError("La priorité et la portée doivent être positives")
    
    # Si l'exposition est sous la priorité, rien n'est cédé
    if exposition <= priorite:
        return 0.0
    
    # Calcul de la part au-dessus de la priorité
    montant_au_dessus_priorite = exposition - priorite
    
    # Le montant cédé est plafonné par la portée
    return min(montant_au_dessus_priorite, portee)


def main():
    print("=== Système de réassurance ===\n")
    
    # Exemple avec quote-part
    exposition_exemple = 1000000.0
    print(f"Exposition: {exposition_exemple:,.2f} €")
    
    print("\n--- Quote-part 30% ---")
    cession_qp = quote_part(exposition_exemple, 0.30)
    print(f"Cédé au réassureur: {cession_qp:,.2f} €")
    print(f"Conservé: {exposition_exemple - cession_qp:,.2f} €")
    
    print("\n--- Excess of Loss (1M xs 500K) ---")
    cession_xol = excess_of_loss(exposition_exemple, 500000, 1000000)
    print(f"Cédé au réassureur: {cession_xol:,.2f} €")
    print(f"Conservé: {exposition_exemple - cession_xol:,.2f} €")


if __name__ == "__main__":
    main()
