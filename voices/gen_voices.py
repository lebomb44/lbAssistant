import gtts
import subprocess

def lbsay(text):
    tts = gtts.gTTS(text=text, lang='fr-FR')
    file_mp3 = text + ".mp3"
    file_wav = text + ".wav"
    tts.save(file_mp3)
    subprocess.check_call('lame --decode "' + file_mp3 + '" "' + file_wav + '"', shell=True)
    print("File " + file_wav)

lbsay("La requete a échoué")
lbsay("La pompe est en marche")
lbsay("La pompe est arrêtée")
lbsay("L'arrosage sur le coté est en marche")
lbsay("L'arrosage sur le coté est arrêtée")
lbsay("L'arrosage est est en marche")
lbsay("L'arrosage est est arrêtée")
lbsay("L'arrosage ouest est en marche")
lbsay("L'arrosage ouest est arrêtée")
lbsay("L'arrosage sud est en marche")
lbsay("L'arrosage sud est arrêtée")
lbsay("La pompe et l'eau du potager sont en marche")
lbsay("La pompe et l'eau du potager sont arrêtés")
lbsay("Ouverture des volets du salon")
lbsay("Fermeture des volets du salon")
lbsay("Ouverture de tous les volets")
lbsay("Fermeture de tous les volets")
#lbsay("La température est de, " + w1Temp.read_temp() + " degrés Celsius", speed=80)
#lbsay("La température extérieure est de, " + temp + " degrés Celsius", speed=80)
#lbsay(value)
lbsay("Tous les systèmes sont opérationnels")
lbsay("Redémarrage de l'assistant en cours")
lbsay("Démarrage de l'alarme")
#lbsay(str(i), speed=80)
lbsay("L'alarme est allumée")
lbsay("L'alarme est arrêtée")
lbsay("La maison est sécurisée")
lbsay("Les notifications sont en marche")
lbsay("Les notifications sont arrêtées")
lbsay("Les notifications sont en marche")
lbsay("Les notifications sont arrêtées")
lbsay("L'arrosage automatique est activé. Démarrage cette nuit à une heure")
lbsay("L'arrosage automatique est désactivé")
lbsay("Impossible de mettre la radio")

