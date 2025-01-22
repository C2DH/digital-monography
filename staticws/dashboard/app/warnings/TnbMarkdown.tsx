import './github-markdown-css.css';
import markdownit from 'markdown-it';


export default function TnbMarkdown({ content }: { content: string }) {
    const md = markdownit();
    const html = md.render(content);
    return (
        <div
            className="markdown-body"
            dangerouslySetInnerHTML={
                { __html: html }
            }>
        </div>
    )
}
