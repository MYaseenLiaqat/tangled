import { Link } from "react-router-dom";

export function Brand({ to }: { to?: string }) {
  const inner = <><span className="brand-mark" aria-hidden="true">t</span><span>Tangled</span></>;
  return to ? <Link className="brand" to={to}>{inner}</Link> : <span className="brand">{inner}</span>;
}
