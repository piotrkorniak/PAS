Serwer podczas uruchomienia tworzy na dysku C: folder "Synchronizacja", który zawiera foldery zarejestrowanych użytkowników.
Aby uruchomić serwer należy użyć komendy:
	- python Serwer.py
	
Aby uruchomić klienta należy zainstalować .NET 5.0 Runtime (https://aka.ms/dotnet-core-applaunch?framework=Microsoft.NETCore.App&framework_version=5.0.0&arch=x64&rid=win10-x64)
a następnie użyć komendy (na pliku znajdującym się \PAS-main\Client\Plik wykonywalny):
	- ./Client.exe [nr.id uruchamianego klienta]

Przy pierwszym uruchomieniu podając login i hasło, klient tworzy folder od nazwy podanego argumentu, (C:/synchronizacjaKlient/_nr.id_/login) na którym działała będzie synchronizacja.
Podanie niezarejestrowanego loginu przy każdym kolejny włączeniu programu będzie skutkowało utworzeniem nowego konta i folderu.
Dodając pliki do folderu C:/synchronizacjaKlient/_nr.id_/login przesyłane są automatycznie do serwera, który przesyła je do wszystkich zalogowanych na to samo konto klientów.