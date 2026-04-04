import { useState } from "react";
import api from "../api/axios"


function Register() {
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")

    const registerUser = async (e) => {
        e.preventDefault()
        const response = await api.post("/auth/register", {
            //request body thats gonna go to backend in json format
            username: username,
            password: password,
            confirm_password: confirmPassword
        })
    }

    return (
        <form onSubmit={registerUser}
        className="flex flex-col gap-4 p-6 bg-gray-60 rounded-xl">
            <input placeholder="username"
            onChange={e => setUsername(e.target.value)}/>
            <input placeholder="password"
            onChange={e => setPassword(e.target.value)}/>
            <input placeholder="confirm password"
            onChange={e => setConfirmPassword(e.target.value)}/>
            <button type="submit"> Register </button>
        </form>
    );
}


export default Register;