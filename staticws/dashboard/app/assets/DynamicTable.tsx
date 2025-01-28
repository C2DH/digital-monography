'use client'

import { useCallback, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header, SearchBar } from "./../_components/TnbTable";
import TnbBookNav from "./../_components/TnbBookNav";

type IAssetRecord = {
    link: string,
    name: string,
    alttext: string,
    caption: string,
    location: string,
    licensename: string,
    isColor?: boolean,
    isOnPaper: boolean,
    isReady: boolean,
}

function getNestedStr(rec: any, attr: string): string {
    const dataType = "S";
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], dataType)) {
        return rec.M[attr][dataType];
    } else {
        return "";
    }
}

function getNestedBool(rec: any, attr: string): boolean | undefined {
    const dataType = "BOOL";
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], dataType)) {
        return (rec.M[attr][dataType]);
    } else {
        return undefined;
    }
}

function getStringForHtml(key: string, val: string | boolean | undefined): string | boolean | undefined {
    if (["isColor", "isOnPaper", "isReady"].includes(key)) {
        switch (val) {
            case true:
                return "✅";
            case false:
                return "❌";
            case undefined:
                return "❓";
            default:
                return "❓";
        }
    } else {
        return val;
    }
}

function getHyperlink(slug: string | null, inputFieldVal: string): string {
    if (slug == null || !inputFieldVal) {
        return "#";
    } else if (inputFieldVal.startsWith("https:") || inputFieldVal.startsWith("http:")) {
        return inputFieldVal
    }
    return `asset?slug=${slug}&pk=${btoa(slug + "/" + inputFieldVal)}`;
}

function getLastPart(s: string): string {
    let split = s.split("/");
    return split[split.length - 1];
}

function getColumnSummary(col: string, isColorSum: number,
    isOnPaperSum: number, isReadySum: number, tableLength: number): JSX.Element {
    if (col == "isColor") {
        return <th key={`${col}-sum`}>{isColorSum}/<small>{tableLength}</small></th>;
    } else if (col == "isOnPaper") {
        return <th key={`${col}-sum`}>{isOnPaperSum}/<small>{tableLength}</small></th>;
    } else if (col == "isReady") {
        return <th key={`${col}-sum`}>{isReadySum}/<small>{tableLength}</small></th>;
    } else {
        return <th key={`${col}-sum`}>{" "}</th>;
    }
}

// function getAsHtml(s: string): string {
//     if (s.toLowerCase().endsWith(".docx")) {
//         return s.substring(0, s.length - 5) + ".html";
//     } else if (s.toLowerCase().endsWith(".ipynb")) {
//         return s.substring(0, s.length - 6) + ".html";
//     } else {
//         return s;
//     };
// }

// see https://monsterlessons-academy.com/posts/custom-react-table-with-filter-and-sorting
export default function DynamicTable() {
    const searchParams = useSearchParams();
    const slug = searchParams?.get("slug");
    const dbTable = "dgtmon-dev-dyndb-assets-tbl";

    const [tableData, setTableData] = useState<IAssetRecord[]>([]);
    const [isColorSum, setIsColorSum] = useState<number>(0);
    const [isOnPaperSum, setIsOnPaperSum] = useState<number>(0);
    const [isReadySum, setIsReadySum] = useState<number>(0);
    const [sorting, setSorting] = useState({ column: "location", order: "asc" });
    const [searchValue, setSearchValue] = useState("");
    const columns = ["link", "name", "location", "alttext", "caption", "licensename", "isColor", "isOnPaper", "isReady"];
    const sortTable = (newSorting) => {
        setSorting(newSorting);
    };
    const searchTable = (newSearchValue: string) => {
        setSearchValue(newSearchValue);
    };

    const fetchRecords = useCallback(async (pk: string) => {
        try {
            setIsColorSum(0);
            setIsOnPaperSum(0);
            setIsReadySum(0);
            const endpoint = "https://20cks5gkc3.execute-api.eu-west-1.amazonaws.com";
            const resp = await fetch(`${endpoint}/test/assets?slug=${pk}`);
            const respJson = await resp.json();
            const items = respJson.Items || [];
            const formatedData: IAssetRecord[] = [];
            for (let i = 0; i < items.length; i++) {
                let records = items[i].records?.L || [];
                for (let j = 0; j < records.length; j++) {
                    const digitalinput = getLastPart(getNestedStr(records[j], "digitalinput"));
                    const paperinput = getLastPart(getNestedStr(records[j], "paperinput"));
                    const alttext = getNestedStr(records[j], "alttext");
                    const caption = getNestedStr(records[j], "caption");
                    const location = getLastPart(getNestedStr(records[j], "location"));
                    const licensename = getNestedStr(records[j], "licensename");
                    const isColor = getNestedBool(records[j], "iscolor");
                    const isReady = getNestedBool(records[j], "isready") || false;
                    const isOnPaper = paperinput != "" ? true : false;
                    if (digitalinput != paperinput && paperinput != "") {
                        if (isColor) {
                            setIsColorSum(n => n + 1);
                        }
                        if (isOnPaper) {
                            setIsOnPaperSum(n => n + 1);
                        }
                        if (isReady) {
                            setIsReadySum(n => n + 1);
                        }
                        formatedData.push({
                            link: getHyperlink(slug, getNestedStr(records[j], "paperinput")),
                            name: paperinput,
                            alttext: alttext,
                            caption: caption,
                            location: location,
                            licensename: licensename,
                            isColor: isColor,
                            isOnPaper: isOnPaper,
                            isReady: isReady,
                        });
                    }
                    if (isColor) {
                        setIsColorSum(n => n + 1);
                    }
                    if (isOnPaper) {
                        setIsOnPaperSum(n => n + 1);
                    }
                    if (isReady) {
                        setIsReadySum(n => n + 1);
                    }
                    formatedData.push({
                        link: getHyperlink(slug, getNestedStr(records[j], "digitalinput")),
                        name: digitalinput,
                        alttext: alttext,
                        caption: caption,
                        location: location,
                        licensename: licensename,
                        isColor: isColor,
                        isOnPaper: isOnPaper,
                        isReady: isReady,
                    });
                }
            }
            setTableData(formatedData);
            console.log("formatedData");
            console.log(formatedData);
        } catch (err) {
            console.log("Error", err);
        }
    }, [slug]);

    useEffect(() => {
        if (slug) {
            fetchRecords(slug);
        }
    }, [fetchRecords, slug]);

    useEffect(() => {
        if (sorting.column == "caption") {
            tableData.sort((a: IAssetRecord, b: IAssetRecord) => {
                const re = /\d+/g
                let numA = re.test(a["caption"]) ? Number(a["caption"].match(re)![0]) : Infinity;
                let numB = re.test(b["caption"]) ? Number(b["caption"].match(re)![0]) : Infinity;
                if (sorting.order == "asc") {
                    return (numA > numB ? 1 : -1)
                } else {
                    return (numA < numB ? 1 : -1)
                }
            });
        } else {
            if (sorting.order == "asc") {
                tableData.sort((a: IAssetRecord, b: IAssetRecord) => (a[sorting.column] > b[sorting.column] ? 1 : -1));
            } else {
                tableData.sort((a: IAssetRecord, b: IAssetRecord) => (a[sorting.column] < b[sorting.column] ? 1 : -1));
            }
        }
    }, [sorting, tableData])

    // useEffect(() => {
    //     console.log("searchValue", searchValue)
    // }, [searchValue])

    return (
        <>
            <div>
                {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
                {/* <SearchBar searchTable={(searchTable)} /> */}
                <table className="table table-striped">
                    <Header columns={columns} sorting={sorting} sortTable={sortTable} />
                    <tbody>
                        {tableData && <tr>{columns.map((col) => (getColumnSummary(col, isColorSum, isOnPaperSum, isReadySum, tableData.length)))}</tr>}
                        {tableData.map((record, idx) => (
                            <tr key={idx}>
                                {columns.map((column) => (column === "link" ?
                                    <td key={column}>
                                        <a className="btn btn-outline-secondary btn-sm"
                                            href={record[column]}
                                            role="button">▶</a>
                                    </td> : <td key={column} className="dgt-mon-table-cell">
                                        {getStringForHtml(column, record[column])}
                                    </td>
                                )
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </>
    )
}
