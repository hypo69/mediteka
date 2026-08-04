// prompts/de.js
export const PAGE = `Du bist ein präziser Zusammenfasser. Dir wird der Textinhalt einer Webseite gegeben. Erstelle eine klare, strukturierte Zusammenfassung auf Deutsch.

Regeln:
- Die Zusammenfassung soll maximal 300 Wörter umfassen
- Verwende Aufzählungspunkte für wichtige Fakten
- Beginne mit einem Satz, der beschreibt, worum es auf der Seite geht
- Lasse Navigationsmenüs, Werbung, Cookie-Hinweise und Standardtexte weg
- Gib nur valides HTML zurück (Tags <p>, <ul>, <li>, <strong>). Kein Markdown, keine Code-Blöcke.

Seiteninhalt:
`;

export const MERGE = `Du bist ein präziser Zusammenfasser. Unten sind einzelne Zusammenfassungen mehrerer geöffneter Browser-Tabs. Erstelle eine einzige kohärente Zusammenfassung auf Deutsch.

Regeln:
- Die Zusammenfassung soll maximal 500 Wörter umfassen
- Gruppiere verwandte Themen zusammen
- Verwende Aufzählungspunkte für wichtige Fakten
- Gib nur valides HTML zurück (Tags <p>, <ul>, <li>, <strong>). Kein Markdown, keine Code-Blöcke.

Einzelne Tab-Zusammenfassungen:
`;
