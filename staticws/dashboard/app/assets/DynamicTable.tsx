'use client'

import { Fragment } from 'react';
import { useCallback, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Header, SearchBar } from "./../_components/TnbTable";
import TnbBookNav from "./../_components/TnbBookNav";

type IOpenedItem = {
    [s3Key: string]: boolean;
}

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
    s3Key: string,
    exists: boolean,
    size?: string,
    mtime?: string,
}

function getNestedStr(rec: any, attr: string): string {
    const dataType = "S";
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], dataType)) {
        return rec.M[attr][dataType];
    } else {
        return "";
    }
}

function getNestedNum(rec: any, attr: string): number | undefined {
    const dataType = "N";
    if (rec && rec.M && Object.hasOwn(rec.M, attr) && Object.hasOwn(rec.M[attr], dataType)) {
        return (rec.M[attr][dataType]);
    } else {
        return undefined;
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
    if (["isColor", "isOnPaper", "isReady", "exists"].includes(key)) {
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

function getImgSrc(slug: string | null, inputFieldVal: string): string {
    const bucket = "https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com";
    if (slug == null || !inputFieldVal) {
        return "";
    } else if (inputFieldVal.startsWith("https:") || inputFieldVal.startsWith("http:")) {
        return "";
    } else {
        return `${bucket}/read/${slug + "/" + inputFieldVal}`;
    }
}

function formatBytes(bytes: number | undefined, decimals = 2): string {
    if (typeof bytes == "undefined" || !+bytes) return '0 Bytes'
    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

function getLastPart(s: string): string {
    let split = s.split("/");
    return split[split.length - 1];
}

function getColSums(col: string, isColorSum: number,
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

function getDate(val: string): string {
    if (!val) return "";
    return new Date(Number(val)).toUTCString();
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

    const [imgOpenedMap, setImgOpenedMap] = useState<IOpenedItem>({});
    const [tableData, setTableData] = useState<IAssetRecord[]>([]);
    const [isColorSum, setIsColorSum] = useState<number>(0);
    const [isOnPaperSum, setIsOnPaperSum] = useState<number>(0);
    const [isReadySum, setIsReadySum] = useState<number>(0);
    const [sorting, setSorting] = useState({ column: "location", order: "asc" });
    const [searchValue, setSearchValue] = useState("");
    const columns = ["link", "name", "location", "alttext", "caption", "licensename", "isColor", "isOnPaper", "exists", "isReady"];
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
            let s3Key = "";
            const imgOpened = {};
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
                        s3Key = getImgSrc(slug, getNestedStr(records[j], "paperinput"));
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
                            s3Key: s3Key,
                            exists: getNestedBool(records[j], "digitalexists") || false,
                            size: formatBytes(getNestedNum(records[j], "digitalsize")),
                            mtime: getDate(getNestedStr(records[j], "digitalmtime")),
                        });
                        imgOpened[s3Key] = false;
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
                    s3Key = getImgSrc(slug, getNestedStr(records[j], "digitalinput"));
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
                        s3Key: s3Key,
                        exists: getNestedBool(records[j], "paperexists") || false,
                        size: formatBytes(getNestedNum(records[j], "papersize")),
                        mtime: getDate(getNestedStr(records[j], "papermtime")),
                    });
                    imgOpened[s3Key] = false;
                }
            }
            setTableData(formatedData);
            // console.log("imgOpened", imgOpened);
            setImgOpenedMap(imgOpened);
            // console.log("imgOpenedMap", imgOpenedMap);
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
            console.log("tableData", tableData);
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
   
    useEffect(() => {
        require("bootstrap/dist/js/bootstrap.bundle.min.js");
    }, []);

    return (
        <>
            <div>
                {slug && <TnbBookNav slug={slug} color="secondary"></TnbBookNav>}
                {/* <SearchBar searchTable={(searchTable)} /> */}
                <table className="table table-striped accordion">
                    <Header columns={columns} sorting={sorting} sortTable={sortTable} />
                    <tbody>
                        {tableData && <tr>{columns.map((col) => (
                        getColSums(col, isColorSum, isOnPaperSum, isReadySum, tableData.length)
                        ))}</tr>}
                        {tableData.map((record, idx) => (
                            <Fragment key={`fragment-${idx}`}>
                                <tr key={idx}
                                    data-bs-toggle="collapse"
                                    data-bs-target={`#details-${idx}`}
                                    >
                                    {columns.map((column) => (column === "link" ?
                                        <td key={column}>
                                            <a className="btn btn-outline-secondary btn-sm"
                                            role="button"
                                            onClick={() => {
                                                setImgOpenedMap({
                                                    ...imgOpenedMap,
                                                    [record.s3Key]: true,
                                                });
                                            }}
                                            >▶</a>
                                        </td> : <td
                                            key={column}
                                            className="dgt-mon-table-cell">
                                            {getStringForHtml(column, record[column])}
                                        </td>
                                    )
                                    )}
                                </tr>
                                <tr key={`details-${idx}`}
                                    id={`details-${idx}`}
                                    className="collapse accordion-collapse">
                                    <td colSpan={columns.length/2}>
                                        {record.s3Key && <h6>{record["caption"]}</h6>}
                                        {/* {record.s3Key && imgOpenedMap[record.s3Key] && <img */}
                                        {record.s3Key && <img
                                                src={record.s3Key}
                                                alt=""
                                                className="img-fluid float-left">
                                            </img>}
                                    </td>
                                    {record.mtime && <td colSpan={columns.length/2}>
                                        Size: {record.size}
                                        Last modified: {record.mtime}
                                    </td>}
                                </tr>
                            </Fragment>
                        ))}
                    </tbody>
                </table>
            </div>
        </>
    )
}
