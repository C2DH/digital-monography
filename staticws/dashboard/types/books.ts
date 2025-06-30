export type IAlert = {
    id: "" | "auth-rejected" | "verif-warning" | "pipeline-fail",
    icon: "" | "❌" | "⚠",
    color: "success" | "danger" | "warning",
    heading: string,
    message: string,
}

export type IBook = {
    authors: string,
    slug: string,
    title: string,
    alert: IAlert,
}

export function getAlert(alert: string): IAlert {
    if (alert == "auth-rejected") {
        return {
            id: alert,
            icon: "❌",
            color: "danger",
            heading: "Access denied. System rejected changes from unauthenticated user.",
            message: "The output will not show the latest version of the manuscript. Login in and reupload.",
        }
    } else if (alert == "verif-warning") {
        return {
            id: alert,
            icon: "⚠",
            color: "warning",
            heading: "System encountered serious issues with the manuscript.",
            message: 'We advise to navigate to the "Warnings" section and to fix them before continuing.',
        }
    } else if (alert == "pipeline-fail") {
        return {
            id: alert,
            icon: "❌",
            color: "danger",
            heading: "Processing the manuscript failed.",
            message: "The output might not show the latest version of the manuscript due to the error.",
        }
    } else {
        return {
            id: "",
            icon: "",
            color: "success",
            heading: "",
            message: "",
        }
    }
}
