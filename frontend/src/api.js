export async function 取(路径) {
  const r = await fetch(`/api${路径}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
export async function 递(路径, 体) {
  const r = await fetch(`/api${路径}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(体 ?? {}),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
