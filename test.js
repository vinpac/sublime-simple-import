import AppDispatcher from "../dispatchers/AppDispatcher";
import React from "react";
import {ActionTypes} from "../constants/AppConstants";
import BaseStore from "./stores/BaseStore";





export default class LoginStore extends BaseStore{

	constructor() {
		super();



		// only an example ...
		var self = this;


		AppDispatcher.register();
	}
}