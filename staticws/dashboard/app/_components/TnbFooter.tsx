import "./../_styles/footer.css";

export default function TnbFooter() {
    const year = new Date().getFullYear();
    return (<footer className="footer">
        <div className="container">
            <span className="text-muted">By Pawel Kaminski © Copyright {year}.</span>
        </div>
    </footer>)
}
