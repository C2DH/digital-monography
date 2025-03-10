import {
    Row,
} from '@tanstack/react-table';
import { IAsset, ITableRow, IRef, IS3Object } from "./types";
import React from 'react';

const READ_BUCKET = "https://cpy-dgtmon-dev-staticws-wip.s3.eu-west-1.amazonaws.com";

export const AssetDetails = (props: { row: Row<ITableRow>, assetMetadata: IAsset[], assetS3List: IS3Object[], refMetadata: IRef[] }) => {
    const { row, assetMetadata, assetS3List, refMetadata } = props;
    const pk = row.original.pk;
    const asset = assetMetadata.find((asset) => asset.pk == pk);
    if (!asset) {
        return <></>
    }
    let s3object: IS3Object | undefined = assetS3List.find((s3obj) => s3obj.Key == `${asset.slug}/${asset.fp}`);
    const refs = asset && asset.target ? refMetadata.filter((ref) => { ref.asset_id == pk }) : null;
    // NOTE: maybe instead of reading from staticws bucket we should read from upload via gpu?
    const imgSrc = asset ? `${READ_BUCKET}/read/${asset.slug}/${asset.fp}` : "";
    // return `asset?slug=${slug}&pk=${btoa(slug + "/" + inputFieldVal)}`; // maybe via backend is better?
    const exists = s3object && s3object.Size > 1;
    const refsFound = refs && (refs?.length || 0) > 0;
    return (
        <>
            <div className="container">
                {!exists && <div className="alert alert-danger" role="alert">
                    The file refered to in the document was <b>not found</b>.
                </div>}
                {exists && <div className="row">
                    <div className="col">
                        <h5>{asset.caption}</h5>
                        {imgSrc && <img
                            src={imgSrc} alt="" className="img-fluid float-left"></img>}
                        <ul className="list-group list-group-horizontal">
                            <li className="list-group-item">
                                Size: {s3object.SizeAsStr}
                            </li>
                            <li className="list-group-item">
                                Last modified: {s3object.LastModified.toLocaleString()}
                            </li>
                            <li className="list-group-item">
                                Ready? {asset.is_ready ? "✅" : "❌"}
                            </li>
                        </ul>
                    </div>
                    <div className="col">
                        <h4>Metadata</h4>
                        <dl>
                            {Object.entries(asset).map(([k, v]) => <React.Fragment
                                key={`${asset.pk}-${k}`}>
                                <dt>{k}</dt>
                                <dd>{v?.toString()}</dd>
                            </React.Fragment>)}
                            {Object.entries(s3object).map(([k, v]) => <React.Fragment
                                key={`${s3object.ETag}-${k}`}>
                                <dt>{k}</dt>
                                <dd>{v?.toString()}</dd>
                            </React.Fragment>)}
                        </dl>
                    </div>
                </div>}
                <h4>References</h4>
                {!refsFound && <p>No references have been found that point to this asset.</p>}
                {refsFound && <div>
                    <p>Found the following references pointing to this asset:</p>
                    <ul>
                        {refs.map((ref) => <li key={ref.pk}>
                            {JSON.stringify(ref, null, 2)}
                        </li>)}
                    </ul>
                </div>}
            </div>
        </>
    )
}
