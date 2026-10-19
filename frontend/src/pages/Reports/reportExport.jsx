import { renderToStaticMarkup } from "react-dom/server";
import { PrescriptionReport } from "./PrescriptionReport";

function documentHtml(report) {
  return '<!doctype html><html><head><meta charset="utf-8"><title>Prescription report</title><style>body{font:14px Arial,sans-serif;color:#193744;margin:32px}h2{font-size:26px}p{line-height:1.6}section{border:1px solid #ccc;padding:16px;margin:16px 0;break-inside:avoid}dl>div{display:flex;margin:8px 0}dt{font-weight:bold;width:150px;flex-shrink:0}dd{margin:0;white-space:pre-wrap;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse}th,td{padding:10px;border:1px solid #ccc;text-align:left}thead{display:table-header-group}@page{margin:15mm}</style></head><body>' + renderToStaticMarkup(<PrescriptionReport report={report} />) + '</body></html>';
}

export function downloadReport(report) {
  const url = URL.createObjectURL(new Blob([documentHtml(report)], { type: "text/html;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `prescription-report-${report.patient.patient_id || "patient"}.html`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function printReport(report) {
  const frame = document.createElement("iframe");
  frame.style.cssText = "position:fixed;width:0;height:0;border:0";
  frame.title = "Print prescription report";
  frame.onload = () => {
    frame.contentWindow.focus();
    frame.contentWindow.print();
  };
  frame.srcdoc = documentHtml(report);
  document.body.appendChild(frame);
  setTimeout(() => frame.remove(), 60000);
}
