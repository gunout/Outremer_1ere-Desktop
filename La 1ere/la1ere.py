import gi
import subprocess
import os
import configparser
import threading

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

class OutreMerRadioApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Outre-Mer La 1ère")
        self.set_default_size(400, 200)  # Taille de la fenêtre réduite

        # Définir l'icône de l'application
        self.set_icon_from_file("play.png")  # Utiliser play.png comme icône de l'application

        # Liste des stations Outre-Mer La 1ère
        self.stations = {
            "Guadeloupe La 1ère": "https://guadeloupe.ice.infomaniak.ch/guadeloupe-128.mp3",
            "Martinique La 1ère": "https://martinique.ice.infomaniak.ch/martinique-128.mp3",
            "Guyane La 1ère": "https://guyane.ice.infomaniak.ch/guyane-128.mp3",
            "La Réunion La 1ère": "https://reunion.ice.infomaniak.ch/reunion-128.mp3",
            "Mayotte La 1ère": "https://mayotte.ice.infomaniak.ch/mayotte-128.mp3",
            "Nouvelle-Calédonie La 1ère": "https://nouvelle-caledonie.ice.infomaniak.ch/nouvelle-caledonie-128.mp3",
            "Polynésie La 1ère": "https://polynesie.ice.infomaniak.ch/polynesie-128.mp3",
            "Wallis et Futuna La 1ère": "https://wallisetfutuna.ice.infomaniak.ch/wallisetfutuna-128.mp3",
            "Saint-Pierre et Miquelon La 1ère": "https://saint-pierreetmiquelon.ice.infomaniak.ch/saint-pierreetmiquelon-128.mp3",
        }

        # Charger les préférences
        self.config_file = os.path.expanduser("~/.outremer_radio.conf")
        self.config = configparser.ConfigParser()
        self.load_preferences()

        # Créer une boîte verticale pour organiser les widgets
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(self.box)

        # Appliquer un style CSS simplifié
        self.apply_css()

        # Menu déroulant pour choisir la station
        self.station_combo = Gtk.ComboBoxText()
        for station in self.stations:
            self.station_combo.append_text(station)
        self.station_combo.set_active(self.config.getint("Preferences", "station_index", fallback=0))
        self.station_combo.connect("changed", self.on_station_changed)
        self.box.pack_start(self.station_combo, False, False, 0)

        # Bouton pour démarrer/arrêter la radio
        self.play_button = Gtk.Button()
        self.play_button.set_image(Gtk.Image.new_from_file("play1.png"))  # Utiliser play1.png comme icône du bouton
        self.play_button.set_always_show_image(True)  # Toujours afficher l'icône
        self.play_button.connect("clicked", self.on_play_button_clicked)
        self.box.pack_start(self.play_button, False, False, 0)

        # Label pour afficher "Play" ou "Stop" sous le bouton
        self.play_stop_label = Gtk.Label(label="Play")
        self.play_stop_label.set_name("play-stop-label")  # Pour appliquer un style CSS spécifique
        self.box.pack_start(self.play_stop_label, False, False, 0)

        # Curseur de volume
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.volume_scale.set_value(self.config.getfloat("Preferences", "volume", fallback=50))
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        self.box.pack_start(self.volume_scale, False, False, 0)

        # Variable pour suivre l'état de la radio
        self.radio_playing = False
        self.process = None

        # Intercepter l'événement de fermeture de la fenêtre
        self.connect("delete-event", self.on_window_delete)

    def apply_css(self):
        """Applique un style CSS simplifié."""
        css = """
        window {
            background-color: #000000;  /* Fond noir */
            color: #ffffff;  /* Texte en blanc */
            font-family: 'Courier New', monospace;
        }
        button {
            background-color: #ffff00;  /* Fond jaune */
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }
        button:hover {
            background-color: #ffff99;  /* Jaune plus clair au survol */
        }
        scale trough {
            background-color: #333333;  /* Fond gris foncé pour la barre de volume */
        }
        scale highlight {
            background-color: #ffff00;  /* Jaune néon pour la partie remplie */
        }
        #play-stop-label {
            color: #ffffff;  /* Texte en blanc */
            font-size: 14px;
            font-weight: bold;
            margin-top: 5px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def load_preferences(self):
        """Charge les préférences depuis le fichier de configuration."""
        if not os.path.exists(self.config_file):
            self.config["Preferences"] = {"station_index": "0", "volume": "50"}
            self.save_preferences()
        else:
            self.config.read(self.config_file)

    def save_preferences(self):
        """Sauvegarde les préférences dans le fichier de configuration."""
        with open(self.config_file, "w") as f:
            self.config.write(f)

    def on_play_button_clicked(self, button):
        if not self.radio_playing:
            # Démarrer la radio avec VLC
            station_name = self.station_combo.get_active_text()
            station_url = self.stations.get(station_name)
            if station_url:
                try:
                    self.process = subprocess.Popen(
                        ["vlc", "--intf", "dummy", "--no-video", "--volume", str(int(self.volume_scale.get_value())), station_url],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    self.radio_playing = True
                    self.play_stop_label.set_label("Stop")  # Mettre à jour le label sous le bouton
                except Exception as e:
                    self.show_error_message(f"Erreur : Impossible de démarrer VLC. {str(e)}")
        else:
            # Arrêter la radio
            self.stop_radio()
            self.radio_playing = False
            self.play_stop_label.set_label("Play")  # Mettre à jour le label sous le bouton

    def stop_radio(self):
        """Arrête la radio en tuant le processus VLC."""
        if self.process:
            try:
                self.process.terminate()  # Envoyer SIGTERM
                self.process.wait(timeout=5)  # Attendre la fin du processus
            except subprocess.TimeoutExpired:
                self.process.kill()  # Forcer l'arrêt si nécessaire
            except Exception as e:
                self.show_error_message(f"Erreur : Impossible d'arrêter VLC. {str(e)}")
            finally:
                self.process = None

    def on_station_changed(self, combo):
        """Change la station en cours."""
        if self.radio_playing:
            self.stop_radio()
            self.on_play_button_clicked(None)

    def on_volume_changed(self, scale):
        """Met à jour le volume en utilisant pactl."""
        volume = int(scale.get_value())
        # Ajuster le volume avec pactl
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"])
        # Sauvegarder le volume dans les préférences
        self.config["Preferences"]["volume"] = str(volume)
        self.save_preferences()

    def on_window_delete(self, window, event):
        """Gère l'événement de fermeture de la fenêtre."""
        # Sauvegarder la station sélectionnée
        self.config["Preferences"]["station_index"] = str(self.station_combo.get_active())
        self.save_preferences()
        self.stop_radio()  # Arrêter la radio
        Gtk.main_quit()  # Quitter l'application

    def show_error_message(self, message):
        """Affiche un message d'erreur dans une boîte de dialogue."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

# Lancer l'application
win = OutreMerRadioApp()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()