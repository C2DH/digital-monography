import { useState } from "react";


export const HeaderCell = ({ column, sorting, sortTable }) => {
    const isDescSorting = sorting.column === column && sorting.order === "desc";
    const isAscSorting = sorting.column === column && sorting.order === "asc";
    const futureSortingOrder = isDescSorting ? "asc" : "desc";
    return (
        <th
            key={column}
            className="dgt-mon-table-cell"
            onClick={() => sortTable({ column, order: futureSortingOrder })}
        >
            {column}
            {isDescSorting && <span>▼</span>}
            {isAscSorting && <span>▲</span>}
        </th>
    );
};

export const Header = ({ columns, sorting, sortTable }) => {
    return (
        <thead>
            <tr>
                {columns.map((column) => (
                    <HeaderCell
                        column={column}
                        sorting={sorting}
                        key={column}
                        sortTable={sortTable}
                    />
                ))}
            </tr>
        </thead>
    );
};

export const SearchBar = ({ searchTable }) => {
    const [searchValue, setSearchValue] = useState("");
    const submitForm = (e) => {
        e.preventDefault();
        searchTable(searchValue);
    };
    return (
        <div className="search-bar">
            <form onSubmit={submitForm}>
                <input
                    type="text"
                    placeholder="Search..."
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
                />
            </form>
        </div>
    );
};
