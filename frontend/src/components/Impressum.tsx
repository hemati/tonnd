import { LegalPage, LegalHeading } from './LegalPage'

export function Impressum() {
  return (
    <LegalPage title="Impressum" lastUpdated="April 2026">
      <section>
        <LegalHeading>Angaben gemäß § 5 DDG</LegalHeading>
        <p>Dr. Wahed Hemati</p>
        <p>Radilostraße 35</p>
        <p>60489 Frankfurt am Main</p>
        <p>Deutschland</p>
      </section>

      <section>
        <LegalHeading>Kontakt</LegalHeading>
        <p>E-Mail: info@tonnd.com</p>
      </section>

      <section>
        <LegalHeading>Umsatzsteuer-ID</LegalHeading>
        <p>Umsatzsteuer-Identifikationsnummer gemäß § 27a Umsatzsteuergesetz:</p>
        <p>DE454994696</p>
      </section>

      <section>
        <LegalHeading>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</LegalHeading>
        <p>Dr. Wahed Hemati</p>
        <p>Radilostraße 35</p>
        <p>60489 Frankfurt am Main</p>
      </section>

      <section>
        <LegalHeading>Verbraucherstreitbeilegung</LegalHeading>
        <p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
      </section>

      <section>
        <LegalHeading>Haftungsausschluss</LegalHeading>

        <h3 className="text-white/70 font-medium mt-4 mb-2">Haftung für Inhalte</h3>
        <p>Die Inhalte dieser Website wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen. Als Diensteanbieter sind wir gemäß § 7 Abs. 1 DDG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 DDG sind wir jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.</p>

        <h3 className="text-white/70 font-medium mt-4 mb-2">Haftung für Links</h3>
        <p>Diese Website enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.</p>

        <h3 className="text-white/70 font-medium mt-4 mb-2">Urheberrecht</h3>
        <p>Die durch uns erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen unserer schriftlichen Zustimmung. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet.</p>
      </section>
    </LegalPage>
  )
}
