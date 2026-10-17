"""Génère un atelier entièrement fictif, indépendant des fichiers du TD."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "demo"
EQUIPMENT = [
    ("P01", "Pompe d'alimentation", "Pompe", "Ligne A", ["pompe alimentation", "pompe amont"]),
    ("P02", "Pompe de refroidissement", "Pompe", "Utilités", ["pompe refroidissement"]),
    ("P03", "Pompe de transfert", "Pompe", "Ligne B", ["pompe transfert"]),
    ("P04", "Pompe de circulation", "Pompe", "Ligne B", ["pompe circulation"]),
    ("M01", "Moteur du convoyeur", "Moteur", "Ligne A", ["moteur convoyeur"]),
    ("M02", "Moteur du mélangeur", "Moteur", "Ligne B", ["moteur mélangeur"]),
    ("M03", "Moteur du ventilateur", "Moteur", "Utilités", ["moteur ventilateur"]),
    ("C01", "Compresseur principal", "Compresseur", "Air comprimé", ["compresseur principal"]),
    ("C02", "Compresseur de secours", "Compresseur", "Air comprimé", ["compresseur secours"]),
    ("C03", "Compresseur de ligne", "Compresseur", "Ligne B", ["compresseur de ligne"]),
]

# Incident, équipement, composant, date, symptômes, diagnostic, statut du diagnostic,
# intervention, durée, résultat et constat de contrôle. Tout est fictif.
EVENTS = [
    (101,"P01","RA","2026-01-06","Vibration; Bruit","Usure du roulement","Confirmé","Remplacement du roulement",95,"Résolu confirmé","Les vibrations ont disparu après remplacement et contrôle en fonctionnement."),
    (102,"P02","J","2026-01-10","Fuite","Usure du joint","Confirmé","Remplacement du joint",55,"Résolu confirmé","Aucune fuite n'est constatée lors du contrôle après remplacement."),
    (103,"M01","RA","2026-01-12","Bruit","Non renseigné","Non renseigné","Lubrification",20,"Résolu confirmé","Le bruit n'est plus observé au contrôle. La cause initiale n'a pas été établie."),
    (104,"M02","ROT","2026-01-14","Vibration","Désalignement du rotor","Confirmé","Inspection",40,"Non résolu","Les vibrations persistent après inspection. Un réalignement reste à programmer."),
    (105,"C01","RA","2026-01-16","Vibration; Surchauffe","Usure du roulement","Confirmé","Remplacement du roulement",120,"Résolu confirmé","Le contrôle confirme la disparition des vibrations et le retour à une température habituelle."),
    (106,"C02","J","2026-01-20","Fuite","Rupture du joint","Confirmé","Remplacement du joint",65,"Résolu confirmé","Le contrôle d'étanchéité après remplacement ne révèle plus de fuite."),
    (107,"P01","ROT","2026-01-22","Vibration","Désalignement du rotor","Suspecté","Inspection",35,"Inconnu","Le résultat après inspection n'est pas renseigné. Aucune conclusion de résolution ou de non-résolution."),
    (108,"M01","ROT","2026-01-25","Bruit","Rupture d'une pièce du rotor","Confirmé","Remplacement du rotor",110,"Résolu confirmé","Le bruit a disparu au contrôle après remplacement."),
    (109,"C01","RB","2026-01-28","Bruit","Non renseigné","Non renseigné","Lubrification",25,"Résolu confirmé","Le bruit n'est plus constaté au contrôle. Aucune cause n'a été confirmée."),
    (110,"P02","RA","2026-02-02","Vibration","Non renseigné","Non renseigné","Inspection",30,"Inconnu","Issue non renseignée ; aucune conclusion de résolution ou de non-résolution."),
    (111,"M02","RA","2026-02-04","Vibration","Non renseigné","Non renseigné","Inspection",25,"Non résolu","Le contrôle montre que les vibrations persistent. Le diagnostic reste à établir."),
    (112,"C02","CAP","2026-02-06","Surchauffe","Défaut du capteur","Suspecté","Inspection du capteur",45,"Inconnu","La température affichée paraît anormale ; l'origine du signal et le résultat de l'inspection restent inconnus."),
    (113,"P03","J","2026-02-10","Fuite","Défaut du joint","Suspecté","Inspection",30,"Non résolu","La fuite persiste. L'hypothèse sur le joint doit être vérifiée."),
    (114,"P04","RA","2026-02-12","Vibration; Bruit","Désalignement","Suspecté","Lubrification",25,"Non résolu","Le bruit diminue, mais les vibrations persistent. L'incident n'est pas résolu."),
    (115,"M03","VENT","2026-02-16","Surchauffe","Obstruction de la ventilation","Confirmé","Nettoyage de la ventilation",40,"Résolu confirmé","Le contrôle en fonctionnement confirme le retour à une température habituelle."),
    (116,"C03","RA","2026-02-18","Vibration","Usure du roulement","Suspecté","Lubrification",30,"Non résolu","Les vibrations persistent après lubrification ; l'usure reste à confirmer."),
    (117,"P03","ROT","","Bruit","Non renseigné","Non renseigné","Inspection",35,"Inconnu","La fiche n'est pas datée et le résultat après inspection n'est pas renseigné."),
    (118,"P04","CAP","2026-02-24","Mesure instable","Défaut du capteur","Suspecté","Inspection du capteur",20,"Inconnu","L'affichage est instable. Aucun résultat après intervention n'est documenté."),
    (119,"M03","RA","2026-03-02","Bruit","Usure du roulement","Confirmé","Remplacement du roulement",80,"Résolu confirmé","Le bruit a disparu au contrôle après remplacement."),
    (120,"C03","J","2026-03-05","Fuite","Rupture du joint","Confirmé","Remplacement du joint",60,"Résolu confirmé","Le contrôle confirme l'absence de fuite après remplacement."),
    (104,"M02","ROT","2026-03-08","Vibration","Désalignement du rotor","Confirmé","Réalignement",70,"Résolu confirmé","Suivi du même incident INC104 : les vibrations ont disparu après réalignement et contrôle."),
    (107,"P01","ROT","2026-03-10","Vibration","Désalignement du rotor","Confirmé","Réalignement",65,"Résolu confirmé","Suivi du même incident INC107 : le contrôle après réalignement confirme la disparition des vibrations."),
    (110,"P02","RA","2026-03-12","Vibration","Non renseigné","Non renseigné","Inspection complémentaire",35,"Inconnu","Suivi du même incident INC110. Issue non renseignée ; aucune conclusion de résolution ou de non-résolution."),
    (111,"M02","RA","2026-03-14","Vibration","Usure du roulement","Confirmé","Remplacement du roulement",85,"Résolu confirmé","Suivi du même incident INC111 : disparition des vibrations constatée au contrôle."),
    (112,"C02","CAP","2026-03-16","Surchauffe","Défaut de mesure du capteur","Confirmé","Recalibrage du capteur",50,"Résolu confirmé","Suivi du même incident INC112 : le contrôle de mesure ne retrouve plus l'anomalie d'affichage."),
    (113,"P03","J","2026-03-18","Fuite","Défaut du joint","Confirmé","Remplacement du joint",55,"Résolu confirmé","Suivi du même incident INC113 : le contrôle ne retrouve plus de fuite."),
    (114,"P04","RA","2026-03-20","Vibration; Bruit","Désalignement","Confirmé","Réalignement",75,"Résolu confirmé","Suivi du même incident INC114 : bruit et vibrations ont disparu après réalignement."),
    (116,"C03","RA","2026-03-22","Vibration","Usure du roulement","Confirmé","Remplacement du roulement",100,"Non résolu","Suivi du même incident INC116 : les vibrations persistent malgré le remplacement. Une autre origine reste à rechercher."),
    (121,"P01","J","2026-03-24","Fuite","Usure du joint","Confirmé","Remplacement du joint",50,"Résolu confirmé","Nouvel incident INC121, distinct de l'incident de rotor INC107. Le contrôle confirme l'étanchéité."),
    (122,"C01","RA","2026-03-28","Vibration; Bruit","Usure du roulement","Suspecté","Inspection",30,"Inconnu","Nouvel incident INC122, distinct d'INC105. Issue non renseignée ; aucune conclusion de résolution ou de non-résolution."),
]
COMPONENTS = {"RA":"Roulement A", "RB":"Roulement B", "ROT":"Rotor", "J":"Joint", "CAP":"Capteur", "VENT":"Ventilation"}


def main():
    equipment = [{"id": code, "name": name, "type": kind, "zone": zone,
                  "aliases": aliases, "components": [
                      {"id": f"{code}_{suffix}", "name": label,
                       "type": "Roulement" if suffix in {"RA", "RB"} else label}
                      for suffix, label in COMPONENTS.items() if kind != "Pompe" or suffix != "VENT"]}
                 for code, name, kind, zone, aliases in EQUIPMENT]
    reports = []
    for number, event in enumerate(EVENTS, 101):
        incident, machine, part, date, symptoms, diagnosis, diagnosis_status, action, duration, outcome, control = event
        eq = next(e for e in equipment if e["id"] == machine)
        text = (f"# RAP{number} — {eq['name']} {machine}\n\n"
                "ATELIER FICTIF HORIZON — scénario de démonstration, aucune donnée d'entreprise.\n\n"
                f"Rapport : RAP{number}\nIncident : INC{incident}\nÉquipement : {machine}\n"
                f"Date : {date or 'Non renseignée'}\nComposant : {COMPONENTS[part]} ({machine}_{part})\n"
                f"Symptômes : {symptoms}\nDiagnostic : {diagnosis}\nStatut du diagnostic : {diagnosis_status}\n"
                f"Intervention : {action}\nDurée : {duration} minutes\nRésultat : {outcome}\n"
                f"Constat de contrôle : {control}\n\n"
                f"## Compte rendu\nLe rapport concerne {eq['name'].lower()} ({machine}), zone {eq['zone']}. "
                f"L'épisode INC{incident} porte sur {COMPONENTS[part].lower()} {machine}_{part}. "
                f"Les observations consignées sont : {symptoms.lower()}. {action} a été réalisé(e), "
                f"pour une durée documentée de {duration} minutes. {control}\n")
        reports.append({"filename": f"RAP{number}_{machine}.md", "text": text})
    ROOT.mkdir(exist_ok=True)
    (ROOT / "atelier.json").write_text(json.dumps({"name":"Atelier Horizon", "fictitious":True,
        "equipment":equipment}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "atelier_rapports.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
