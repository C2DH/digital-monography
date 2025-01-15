import './github-markdown-css.css';
import micromarkdown from "micromarkdown";

export default function TnbMarkdown({ content }: { content: string }) {
    const html = micromarkdown.parse(content);
    return (
        <div
            className="markdown-body"
            dangerouslySetInnerHTML={
                { __html: html }
            }>
        </div>
    )
}
