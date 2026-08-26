import React, {useState} from 'react';

function Login(){
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState(null);

  const submit = async (e) =>{
    e.preventDefault();
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    try{
      const res = await fetch('http://localhost:8000/auth/login', {method:'POST', body: form});
      if(!res.ok){ throw new Error('Invalid credentials'); }
      const data = await res.json();
      localStorage.setItem('irbid_token', data.access_token);
      setMsg('تم تسجيل الدخول');
    }catch(err){ setMsg(err.message); }
  }

  return (
    <div style={{maxWidth:400, margin:'30px auto'}}>
      <h2>تسجيل الدخول / Login</h2>
      <form onSubmit={submit}>
        <div>
          <label>البريد الإلكتروني / Email</label>
          <input value={email} onChange={e=>setEmail(e.target.value)} style={{width:'100%'}} />
        </div>
        <div>
          <label>كلمة المرور / Password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} style={{width:'100%'}} />
        </div>
        <button type="submit">تسجيل الدخول</button>
        {msg && <p>{msg}</p>}
      </form>
    </div>
  )
}

export default Login;
