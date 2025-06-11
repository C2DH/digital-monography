import "bootstrap/dist/css/bootstrap.min.css";
import "./_styles/globals.css";
import TnbHeader from "./_components/TnbHeader";
import TnbFooter from "./_components/TnbFooter";

export const metadata = {
  title: "Dashboard for Living Books",
  description: "Dashboard for Living Books by de Gruyter Brill",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className="antialiased"
      >
        <TnbHeader></TnbHeader>
        <main role="main" className="container">
          {children}
        </main>
        <TnbFooter></TnbFooter>
        {/* <script
          src="https://code.jquery.com/jquery-3.7.1.slim.min.js"
          integrity="sha256-kmHvs0B+OpCW5GVHUNjv9rOmY0IvSIRcf7zGUDTDQM8="
          crossOrigin="anonymous"></script> */}
      </body>
    </html>
  );
}
