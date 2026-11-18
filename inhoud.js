// =====================================================================
//  INHOUD — naam van het slachtoffer en de teksten van de lokcodes
// =====================================================================
//
//  De echte inhoud (foto's, gifs, audio, video, YouTube-links) komt uit
//  de map media/. Elk bestand daar krijgt een eigen QR-code.
//  codes.js en media.js worden automatisch gemaakt: niet aanpassen.
//
//  Regels voor dit bestand:
//  - Tekst staat tussen `backticks`.
//  - Vergeet de komma's tussen de blokken niet.
//
// =====================================================================

const HEIDIGOM = "Heidigom";   // naam van het slachtoffer


// ---------------------------------------------------------------------
//  LOKCODES (veel QR-codes per soort, overal verspreid)
// ---------------------------------------------------------------------
//  Bij elke scan wordt willekeurig één van de varianten getoond.
//  Je mag varianten toevoegen of schrappen. {naam} wordt vervangen
//  door de naam (Heidigom).
//
//  De soort "eindeloos" toont een laadbalk die nooit klaar is.

const LOKPAGINAS = {

  fout: {
    emoji: "🚫",
    varianten: [
      { titel: "Ongeldige QR-code", tekst: `Deze code kon niet gelezen worden. Probeer het opnieuw, {naam}.` },
      { titel: "Fout 404", tekst: `Activiteit niet gevonden. Misschien ligt ze onder een andere QR-code.` },
      { titel: "Scan mislukt", tekst: `Je hield je telefoon verkeerd. Of de code. Of allebei.` },
    ],
  },

  volgende: {
    emoji: "👉",
    varianten: [
      { titel: "Bijna!", tekst: `Deze QR-code is maar een tussenstap. Zoek de volgende.` },
      { titel: "Verkeerde code", tekst: `De echte uitleg zit achter een andere QR-code. Ergens in deze kamer. Waarschijnlijk.` },
      { titel: "Niveau 1 voltooid", tekst: `Gefeliciteerd, {naam}. Scan nog een code om niveau 2 te ontgrendelen.` },
    ],
  },

  spot: {
    emoji: "😈",
    varianten: [
      { titel: "Proficiat", tekst: `Je hebt net vrijwillig een QR-code gescand, {naam}. Hoe voelt dat?` },
      { titel: "Leuk weetje", tekst: `Een QR-code kan tot 30% beschadigd zijn en nog steeds werken. Net als jij na vanavond.` },
      { titel: "Applaus", tekst: `Iedereen in de kamer heeft net gezien dat je deze code scande.` },
      { titel: "Bedankt voor je deelname", tekst: `Je gegevens zijn doorgestuurd naar je toekomstige schoonfamilie.` },
    ],
  },

  verlopen: {
    emoji: "⌛",
    varianten: [
      { titel: "QR-code verlopen", tekst: `Deze code was maar 5 minuten geldig. Vraag een nieuwe aan bij de getuige.` },
      { titel: "Sessie verlopen", tekst: `Je hebt te lang getwijfeld voor je scande. Begin opnieuw.` },
    ],
  },

  eindeloos: {
    emoji: "⏳",
    varianten: [
      { titel: "", tekst: `Nog steeds aan het laden. Net als jouw enthousiasme voor QR-codes, {naam}.` },
    ],
  },
};
