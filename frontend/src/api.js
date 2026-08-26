// simple API helper
export async function apiGet(path){
  const token = localStorage.getItem('irbid_token');
  const res = await fetch(`http://localhost:8000${path}`, {headers: { 'Authorization': token ? `Bearer ${token}` : '' }});
  return res.json();
}
