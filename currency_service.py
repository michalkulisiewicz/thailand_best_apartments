from decimal import Decimal
import requests
import time
from typing import Optional, Tuple

class CurrencyService:
    def __init__(self):
        # // Domyślny kurs wymiany THB/PLN
        self.thb_to_pln_rate = Decimal('0.1179')
        self.last_update = None
        
    def get_current_rate(self) -> Tuple[Decimal, Optional[str]]:
        """
        // Pobiera aktualny kurs wymiany
        Returns:
            Tuple[Decimal, Optional[str]]: (kurs wymiany, komunikat błędu jeśli wystąpił)
        """
        try:
            # // Pobierz kurs THB z API NBP
            nbp_url = "http://api.nbp.pl/api/exchangerates/rates/a/thb/"
            response = requests.get(nbp_url)
            
            if response.status_code == 200:
                data = response.json()
                rate = Decimal(str(data['rates'][0]['mid']))
                self.thb_to_pln_rate = rate
                self.last_update = time.time()
                return rate, None
            else:
                return self.thb_to_pln_rate, f"Error fetching rate: {response.status_code}"
                
        except Exception as e:
            return self.thb_to_pln_rate, f"Error updating exchange rate: {str(e)}"
    
    def convert_to_pln(self, thb_amount: float) -> Optional[float]:
        """
        // Konwertuje kwotę z THB na PLN
        Args:
            thb_amount: Kwota w bahtach
        Returns:
            float: Kwota w złotówkach
        """
        if not thb_amount:
            return None
            
        try:
            pln_amount = float(Decimal(str(thb_amount)) * self.thb_to_pln_rate)
            return round(pln_amount, 2)
        except Exception as e:
            print(f"// Błąd konwersji waluty: {str(e)}")
            return None
    
    def get_last_update_time(self) -> Optional[str]:
        """
        // Zwraca czas ostatniej aktualizacji kursu
        """
        if self.last_update:
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_update))
        return None 
