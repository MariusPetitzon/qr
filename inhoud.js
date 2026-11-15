// =====================================================================
//  INHOUD — dit is het enige bestand dat je moet aanpassen
// =====================================================================
//
//  Welke QR-code naar welke pagina gaat, staat in codes.js (automatisch,
//  niet aanpassen). Hier staat alleen WAT er op die pagina's komt.
//
//  Regels:
//  - Tekst staat tussen `backticks`. Een lege regel = nieuwe alinea.
//  - Simpele HTML mag: <b>vet</b>, <i>schuin</i>, <br>.
//  - Vergeet de komma's tussen de blokken niet.
//
// =====================================================================

const HEIDIGOM = "Heidigom";   // naam van het slachtoffer


// ---------------------------------------------------------------------
//  1. DE ECHTE ACTIVITEITEN (één QR-code per activiteit)
// ---------------------------------------------------------------------
//  "gif" mag leeg blijven ("").  "extra" = inklapbare onderdelen, of [].

const ACTIVITEITEN = [
  {
    nummer: 1,
    titel: "Quiz",
    gif: "gifs/01.gif",
    tekst: `Hier komt de uitleg van de quiz.

Elke vraag zit achter een eigen QR-code. Succes, {naam}.`,
    extra: [
      { titel: "Spelregels", tekst: `Regel 1.<br>Regel 2.<br>Regel 3.` },
      { titel: "Wat als je verliest?", tekst: `Een shotje. Of twee.` },
    ],
    // Onderdelen: elk krijgt een EIGEN QR-code (aantal staat in tools/aantallen.json).
    // "beeld" = pad in media/: afbeelding, GIF, audio (.mp3/.m4a) of video (.mp4), of een lijst: ["a.jpg", "b.mp3"].
    onderdelen: [
      {
        titel: "Vraag 1",
        beeld: "media/Quizz/quiz-1.jpg",
        tekst: ``,
        extra: [],
      },
    ],
  },
  { nummer: 2,  titel: "Activiteit 2",  gif: "gifs/02.gif", tekst: `Uitleg van activiteit 2.`,  extra: [] },
  { nummer: 3,  titel: "Activiteit 3",  gif: "gifs/03.gif", tekst: `Uitleg van activiteit 3.`,  extra: [] },
  { nummer: 4,  titel: "Activiteit 4",  gif: "gifs/04.gif", tekst: `Uitleg van activiteit 4.`,  extra: [] },
  { nummer: 5,  titel: "Activiteit 5",  gif: "gifs/05.gif", tekst: `Uitleg van activiteit 5.`,  extra: [] },
  { nummer: 6,  titel: "Activiteit 6",  gif: "gifs/06.gif", tekst: `Uitleg van activiteit 6.`,  extra: [] },
  { nummer: 7,  titel: "Activiteit 7",  gif: "gifs/07.gif", tekst: `Uitleg van activiteit 7.`,  extra: [] },
  { nummer: 8,  titel: "Activiteit 8",  gif: "gifs/08.gif", tekst: `Uitleg van activiteit 8.`,  extra: [] },
  { nummer: 9,  titel: "Activiteit 9",  gif: "gifs/09.gif", tekst: `Uitleg van activiteit 9.`,  extra: [] },
  { nummer: 10, titel: "Activiteit 10", gif: "gifs/10.gif", tekst: `Uitleg van activiteit 10.`, extra: [] },
];


// ---------------------------------------------------------------------
//  2. LOKCODES (veel QR-codes per soort, overal verspreid)
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
