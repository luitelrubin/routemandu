import {combineReducers} from "redux";
import Auth from "./auth";

const rootReducer =  combineReducers({auth:Auth});

export default rootReducer;