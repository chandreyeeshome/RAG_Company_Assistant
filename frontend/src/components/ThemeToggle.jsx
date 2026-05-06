import React, {useContext} from "react"
import "./ThemeToggle.css"
import { AppContext } from "../App"

export const ThemeToggle = () => {
    const {isDark, setIsDark} = useContext(AppContext);
    return(
        <div className="toggleContainer">
            <input 
                type="checkbox"
                id="check"
                className="toggle" 
                onChange={()=>setIsDark(!isDark)}
                checked={isDark}
            />
            <label htmlFor="check"></label>
        </div>
    )
}
