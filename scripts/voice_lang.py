#!/usr/bin/env python3
"""voice_lang.py - language data for the measurements and the rules.

English data stays in stylometry.py, voice_rules.py and voice_rules_reader.py, where it
has always lived. This module holds the German data and the helpers that pick a language.
A profile names its language in "language" ("en" or "de"). Without it the language is English.
German means standard German (Hochdeutsch) only. Stdlib only.
"""

LANGUAGES = ("en", "de")


def lang_of(profile) -> str:
    lang = (profile or {}).get("language", "en")
    return lang if lang in LANGUAGES else "en"


SPACY_MODELS = {"en": "en_core_web_sm", "de": "de_core_news_sm"}

# --- Measurements (stylometry.py) ---

DE_FUNCTION_WORDS = frozenset({
    "aber", "alle", "allem", "allen", "aller", "alles", "als", "also", "am", "an", "andere", "anderen",
    "auch", "auf", "aus", "bei", "beim", "bereits", "bin", "bis", "bist", "bleibt", "da", "dabei", "dadurch",
    "dafür", "dagegen", "damit", "dann", "darauf", "darin", "darum", "das", "dass", "davon", "dazu", "dein",
    "deine", "dem", "den", "denen", "denn", "der", "deren", "des", "dessen", "deshalb", "dich", "die", "dies",
    "diese", "diesem", "diesen", "dieser", "dieses", "dir", "doch", "dort", "du", "durch", "eben", "ein",
    "eine", "einem", "einen", "einer", "eines", "einige", "einmal", "er", "es", "etwa", "etwas", "euch",
    "euer", "für", "gegen", "ganz", "gar", "gerade", "gibt", "habe", "haben", "hat", "hatte", "hätte", "hier",
    "ich", "ihm", "ihn", "ihnen", "ihr", "ihre", "ihrem", "ihren", "ihrer", "im", "immer", "in", "indem",
    "ins", "ist", "ja", "je", "jede", "jedem", "jeden", "jeder", "jedes", "jedoch", "jetzt", "kann", "kein",
    "keine", "keinen", "können", "könnte", "man", "manche", "mehr", "mein", "meine", "meinem", "meinen",
    "meiner", "mich", "mir", "mit", "muss", "müssen", "nach", "nicht", "nichts", "noch", "nun", "nur", "ob",
    "oder", "ohne", "schon", "sehr", "sein", "seine", "seinem", "seinen", "seiner", "seit", "sich", "sie",
    "sind", "so", "sodass", "soll", "sollte", "sondern", "sonst", "über", "um", "und", "uns", "unser",
    "unsere", "unter", "viel", "viele", "vom", "von", "vor", "während", "war", "waren", "warum", "was",
    "weil", "welche", "welcher", "wenn", "wer", "werden", "wie", "wieder", "will", "wir", "wird", "wo",
    "wurde", "wurden", "würde", "zu", "zum", "zur", "zwar", "zwischen",
})

DE_HEDGE_TOKENS = frozenset({
    "vielleicht", "möglicherweise", "eventuell", "wahrscheinlich", "vermutlich", "scheinbar", "anscheinend",
    "offenbar", "eher", "ziemlich", "gewissermaßen", "sozusagen", "womöglich", "tendenziell", "teilweise",
    "irgendwie", "ungefähr", "könnte", "könnten", "dürfte", "dürften", "meist", "meistens", "oft",
    "manchmal", "gelegentlich", "scheint", "scheinen",
})
DE_HEDGE_PHRASES = ["ich denke", "ich glaube", "ich vermute", "in gewisser weise", "bis zu einem gewissen grad",
                    "in vielerlei hinsicht", "im grunde"]
DE_BOOSTER_TOKENS = frozenset({
    "definitiv", "absolut", "sicherlich", "zweifellos", "offensichtlich", "eindeutig", "selbstverständlich",
    "tatsächlich", "wirklich", "völlig", "total", "extrem", "äußerst", "enorm", "unbedingt", "garantiert",
    "bestimmt", "zweifelsohne", "fraglos", "unbestreitbar", "keinesfalls", "niemals",
})

DE_PRONOUN_FIRST_SG = frozenset({"ich", "mich", "mir", "mein", "meine", "meinen", "meinem", "meiner", "meines"})
DE_PRONOUN_FIRST_PL = frozenset({"wir", "uns", "unser", "unsere", "unseren", "unserem", "unserer", "unseres"})
DE_PRONOUN_SECOND = frozenset({"du", "dich", "dir", "dein", "deine", "deinen", "deinem", "deiner", "deines",
                               "euch", "euer", "eure", "euren", "eurem", "eurer"})
DE_PRONOUN_THIRD = frozenset({"er", "ihn", "ihm", "sein", "seine", "seinen", "seinem", "seiner", "seines",
                              "sie", "es", "ihr", "ihre", "ihren", "ihrem", "ihrer", "ihres", "ihnen"})

DE_CONCESSION_WORDS = frozenset({"aber", "jedoch", "allerdings", "obwohl", "obgleich", "wenngleich", "trotzdem",
                                 "dennoch", "doch", "hingegen", "zwar", "trotz", "ungeachtet"})

DE_NOMINAL_SUFFIXES = ("ung", "heit", "keit", "ion", "ität", "ismus", "schaft")

# --- Rules (voice_rules.py) ---

DE_STANCE_OPENERS = ("bemerkenswerterweise", "interessanterweise", "erstaunlicherweise", "überraschenderweise",
                     "bezeichnenderweise", "offensichtlich", "offenkundig", "selbstverständlich", "natürlich",
                     "freilich", "bekanntlich", "zweifellos", "zweifelsohne", "zugegebenermaßen", "ehrlicherweise",
                     "fraglos", "unbestreitbar")

DE_FILLER_OPENERS = (
    "es ist wichtig zu beachten", "es ist wichtig zu erwähnen", "es ist wichtig zu betonen",
    "es ist erwähnenswert", "erwähnenswert ist", "es sei darauf hingewiesen", "es sei angemerkt",
    "es sei erwähnt", "es ist kein geheimnis", "es ist allgemein bekannt", "es versteht sich von selbst",
    "es liegt auf der hand", "in der heutigen schnelllebigen", "in der heutigen digitalen", "in der heutigen zeit",
    "im heutigen digitalen zeitalter", "in einer welt, in der", "immer mehr menschen fragen sich",
    "vergessen sind die zeiten", "ehrlich gesagt", "offen gesagt", "offen gestanden",
    "stand meines letzten wissensupdates", "bis zu meinem letzten update",
    "basierend auf den verfügbaren informationen", "basierend auf verfügbaren informationen",
    "ich hoffe, diese nachricht erreicht sie", "tauchen wir ein", "tauchen sie ein", "tauche ein",
)

DE_PERFORMATIVE = {
    "revolutionieren": "verändern", "revolutioniert": "verändert", "revolutionierte": "veränderte",
    "transformieren": "verändern", "transformiert": "verändert", "entfesseln": "nutzen", "entfesselt": "nutzt",
    "eintauchen": "sich ansehen", "katapultieren": "bringen", "katapultiert": "bringt",
    "unterstreicht": "zeigt", "unterstreichen": "zeigen", "unterstrich": "zeigte",
    "ausschöpfen": "nutzen",
}

DE_SUMMARY_OPENERS = ("zusammenfassend", "abschließend lässt sich", "abschließend kann man", "im großen und ganzen",
                      "alles in allem", "insgesamt lässt sich", "letztendlich lässt sich")

DE_NOT_ONLY = r"\bnicht nur\b.*\bsondern auch\b"
DE_TRICOLON_CONJ = "(?:und|oder|sowie)"
DE_ANTITHESIS_TAIL = r",\s+nicht\s+([^,.;:!?]+?)\s*[.!?]?\s*$"
DE_ANTITHESIS_SHORT = r",\s*nicht\s+\S|\b(?:an)?statt\b|\banstelle\b"
# "statt" is ordinary in a long German sentence, so long prose checks only the ", nicht X." tail
DE_ANTITHESIS_INSTEAD = r"(?!)"
DE_BUILDUP_STORY = r"\berzählt eine \w+ geschichte\b"

DE_LIST_INTRO_WORDS = {"folgende", "folgenden", "folgendes", "folgt", "diese", "dieser", "zwei", "drei", "vier",
                       "fünf", "sechs", "sieben", "acht", "neun", "zehn", "gründe", "schritte", "punkte", "arten",
                       "beispiele", "beispiel", "nämlich", "gehören", "umfasst", "umfassen", "bereiche", "teile",
                       "optionen", "möglichkeiten"}
DE_LABEL_HEAD_DETERMINERS = {"der", "die", "das", "ein", "eine", "einen", "dieser", "diese", "dieses", "unser",
                             "unsere", "mein", "meine", "sein", "seine", "ihr", "ihre", "jeder", "jede"}

# --- Reader rules (voice_rules_reader.py) ---

DE_PARAGRAPH_OPENERS = ("allerdings", "jedoch", "beachten sie aber")
DE_BENEFIT_COMMA = (r",\s*(?:damit (?:sie|du)|sodass (?:sie|du)|so dass (?:sie|du)|was (?:ihnen|dir) ermöglicht|"
                    r"wodurch (?:sie|du))\b[^.!?]*[.!?]?\s*$")
DE_ABSTRACT_NOUNS = {"qualität", "klarheit", "vertrauen", "wachstum", "wirkung", "kraft", "einfachheit",
                     "geschwindigkeit", "erfolg", "wert", "werte", "exzellenz", "innovation", "freiheit", "kontrolle",
                     "ergebnisse", "sicherheit", "zukunft", "leidenschaft", "präzision", "nachhaltigkeit", "effizienz",
                     "verantwortung", "vielfalt"}
DE_FINITE_SIGNALS = {"ist", "sind", "war", "waren", "sein", "hat", "haben", "hatte", "wird", "werden", "wurde", "kann",
                     "können", "soll", "sollte", "muss", "müssen", "darf", "nicht", "ich", "du", "er", "sie", "es",
                     "wir", "ihr", "macht", "bringt", "gibt"}
DE_TAGLINE_STOP = {"und", "oder", "für", "von", "mit", "der", "die", "das", "ein", "eine", "jede", "jeden", "ihre",
                   "unsere", "mehr", "weniger", "in", "im", "auf", "zu", "aus", "durch", "ohne", "bei", "alle", "als"}

# --- German-only rules (voice_rules_de.py) ---

DE_CALQUES = ("sinn machen", "macht sinn", "machen sinn", "machte sinn", "einmal mehr", "am ende des tages",
              "auf das nächste level", "aufs nächste level", "auf ein neues level", "game-changer", "gamechanger",
              "wandteppich", "ein muss für", "eintauchen in")

DE_MECHANICAL_CONNECTIVES = ("darüber hinaus", "des weiteren", "ferner", "überdies", "zudem", "zusätzlich",
                             "außerdem", "infolgedessen", "andererseits")

DE_PARTICIPLE_TAILS = ("hervorhebend", "betonend", "unterstreichend", "widerspiegelnd", "gewährleistend",
                       "verdeutlichend", "ermöglichend", "sicherstellend", "aufzeigend", "demonstrierend",
                       "illustrierend", "signalisierend", "markierend", "festigend", "stärkend", "fördernd")

DE_HEADING_FUNCTION_WORDS = {"Für", "Und", "Oder", "Mit", "Von", "Vom", "Den", "Dem", "Der", "Die", "Das", "Des",
                             "Ein", "Eine", "Einen", "Im", "In", "Auf", "Zu", "Zum", "Zur", "Bei", "Beim", "Aus",
                             "Nach", "Über", "Unter", "Ohne", "Gegen", "Wie", "Was", "Ist", "Sind", "Am", "An", "Als",
                             "Durch", "Um", "Bis", "Seit"}

DE_ASCII_UMLAUT_WORDS = (
    "fuer", "ueber", "ueberhaupt", "koennen", "koennte", "koennten", "muessen", "muesste", "moechte", "moechten",
    "waere", "waeren", "haette", "haetten", "wuerde", "wuerden", "groesse", "groesser", "schoen", "schoene",
    "frueh", "frueher", "spaeter", "natuerlich", "moeglich", "moeglichkeit", "moeglichkeiten", "zurueck",
    "fuehren", "gefuehl", "aendern", "aenderung", "aenderungen", "taeglich", "naechste", "naechsten", "hoeher",
    "pruefen", "pruefung", "ueblich", "oeffentlich", "koerper", "hoeren", "fuenf", "zwoelf", "waehrend",
    "aehnlich", "ueberall", "uebersicht", "tuer", "loesung", "loesungen",
)
DE_SS_WORDS = ("ausserdem", "strasse", "heisst", "grosse", "grossen", "schliesslich", "massnahme", "massnahmen",
               "gemaess", "fuss", "gruesse", "regelmaessig")

MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December|"
          "Januar|Februar|März|Juni|Juli|Oktober|Dezember")

# --- Default German bans (voice_profile.py) ---

DE_BANS = {
    "intensifiers": ["zweifellos", "zweifelsohne", "ohne zweifel", "fraglos", "unbestreitbar", "ungemein", "überaus"],
    "hedge_connectives": ["fairerweise muss man sagen", "der vollständigkeit halber", "wohlgemerkt",
                          "nur damit sie wissen", "nur damit du weißt"],
    "protest_framing": ["das ist kein gimmick", "das ist keine theorie", "nichts davon ist", "das ist kein trick"],
    "meta_commentary": ["gute frage", "tolle frage", "ich helfe gerne", "gerne helfe ich", "ich hoffe, das hilft",
                        "lassen sie mich wissen", "lass mich wissen", "sag mir bescheid", "möchten sie, dass ich",
                        "aber sicher! hier", "klar! hier ist", "natürlich! hier"],
    "evaluative_block": ["innovativ", "bahnbrechend", "revolutionär", "hochmodern", "wegweisend", "zukunftsweisend",
                         "erstklassig", "branchenführend"],
    "evaluative_review": ["leistungsstark", "robust", "umfassend", "nahtlos", "ganzheitlich", "maßgeschneidert",
                          "signifikant", "erheblich", "einzigartig", "bemerkenswert", "beeindruckend", "faszinierend",
                          "essenziell", "facettenreich"],
    "caveat_phrases": ["beachten sie, dass", "bedenken sie", "denken sie daran", "denk daran", "ein hinweis noch",
                       "eine kleine einschränkung", "die ergebnisse können variieren"],
    "extra_phrases": [],
}
