// Initialize variables
FREVIVE_BUILD_TABLE = {
	_unit = call _x; 
	if (_unit==player) then {_id_player=_id}; 
	if (FREVIVE_USE_FLAGS) then {call Format ["FREVIVE_FLAG%1 setFlagOwner %2",_id,_x]}; 

	_list_bodies         set [count _list_bodies        , _unit]; 
	_list_status         set [count _list_status        , -1]; 
	_list_location       set [count _list_location      , [0,0,0]];
	_list_dir            set [count _list_dir           , 0]; 
	_list_side           set [count _list_side          , side _unit]; 
	_list_name           set [count _list_name          , name _unit]; 
	_list_weapons        set [count _list_weapons       , []]; 
	_list_magazines      set [count _list_magazines     , []]; 
	_list_revives_left   set [count _list_revives_left  , FREVIVE_LIMIT]; 
	_list_revive_timeout set [count _list_revive_timeout, -1]; 
	_list_ai_msg         set [count _list_ai_msg        , objNull]; 
	_list_ai_move_time   set [count _list_ai_move_time  , 0]; 
	_list_savior         set [count _list_savior        , -1]; 
	_list_sound_time     set [count _list_sound_time    , 0]; 
	
	_id = _id + 1
};

// When reviving calculate progress and show title from description.ext
FREVIVE_FNC_SHOW_PROGRESS = {
	private ["_percent", "_remainder", "_result"];

	if (player in _this) then {
		_percent = ((_time-((_timing select _i)-FREVIVE_PICKUP_TIME)) / FREVIVE_PICKUP_TIME) * 100;
		
		if (!local (_this select 1)) then {
			_percent = (getDammage (_this select 1)) * 200;
		};
		
		_percent   = _percent - _percent mod 1;
		_remainder = _percent mod 5;
		_result    = _percent - _remainder + (if (_remainder >= (5/2)) then {5} else {0});
		
		if (_result > 100) then {_result=100};
		if (_result < 0) then {_result=0};
		
		cutRsc [Format["FREVIVE_PERCENTAGE_%1",_result], "PLAIN"]
	}
};


// Are two sides friendly with each other 
// Used to determine who can revive, for showing messages, particles, markers, spectator list
FREVIVE_FNC_IS_FRIENDLY = {
	if ((_this select 0) == (_this select 1) || (resistance in _this && civilian in _this)) then {	// if two sides are identical (res and civ are the same side)
		true
	} else {
		"_x in [resistance,civilian]" count _this>0 && "_x in FREVIVE_SIDE_RESISTANCE" count _this>0	// is friendly to resistance
	}
};


// Are two sides friendly with each other and with the player (first argument)
// Used to show messages
FREVIVE_FNC_IS_FRIENDLY_TO_PLR = {
	private ["_friendlies"];
	_friendlies = [_this select 0];
	
	if ((_this select 0) in FREVIVE_SIDE_RESISTANCE) then {
		_friendlies = _friendlies + [resistance,civilian]
	};

	"_x in _friendlies" count _this == 3
};


// Show messages on chat
FREVIVE_FNC_CHAT = {	
	if (FREVIVE_MSG_STYLE >= 0) then {
		private ["_msg_id", "_dead", "_savior", "_source", "_command", "_messages"];
		
		_msg_id   = _this select 0;
		_dead     = _this select 1;
		_savior   = if (count _this>2) then {_this select 2} else {0};
		_source   = _logic;
		_command  = "globalChat";
		_messages = [
			"§ %1 is waiting to be revived",
			"§ %2 is moving to revive %1",
			"§ %1 was revived by %2"
		];
		
		if (FREVIVE_MSG_STYLE == 2) then {
			_messages = [
				"I'm down! Pick me up!",
				"I'm moving to revive %1",
				"I've revived %1"
			];
			
			_source = if (_msg_id==0) then {call (_var_name_list select _dead)} else {call (_var_name_list select _savior)};
			
			if (_sides select _player_id == _sides select _dead) then {
				_command = "sideChat";
			}
		};

		call Format ["_source %1 Format [_messages select _msg_id, _name_list select _dead, _name_list select _savior]", _command]
	}
};


// If class restriction enabled then check if unit is allowed to revive
FREVIVE_FNC_IS_MEDIC = {
	if (FREVIVE_ONLY_MEDIC) then {
		(typeOf _this) in FREVIVE_MEDICS
	} else {
		true
	}
};


// Distance between two points in three dimensions
// Used to determine if a dead body was moved
MATH_DIST3D = {
	private ["_source", "_target"];
	
	_source = _this select 0;
	_target = _this select 1;
	
	sqrt (((_target select 0) - (_source select 0))^2 + ((_target select 1) - (_source select 1))^2+ ((_target select 2) - (_source select 2))^2)
};


// Sort multiple arrays in parallel to the first array
// Used to determine who is closest to the dead body
quicksortM = {
	private ["_array", "_arrays", "_currentARR", "_hi", "_i", "_j", "_k", "_lo", "_mid", "_temp"];
	
	if (format ["%1",QUICKSORT_RECURRENCE] == "scalar bool array string 0xfcffffef") then {
		QUICKSORT_RECURRENCE = 1;
		_arrays = _this;
		_array = _arrays select 0;
		_lo = 0;
		_hi = count _array -1;
		_i = _lo;
		_j = _hi;
	} else {
		QUICKSORT_RECURRENCE = QUICKSORT_RECURRENCE + 1;
		_arrays = _this select 0;
		_array = _arrays select 0;
		_lo = _this select 1;
		_hi = _this select 2;
		_i = _lo;
		_j = _hi;
	};
	
	_mid = (_lo + _hi) / 2;
	_mid = _mid - (_mid mod 1);
	_mid = _array select _mid;
	
	while "_i <= _j" do {
		while "  (_array select _i) < _mid  " do {_i=_i+1};
		while "  (_array select _j) > _mid  " do {_j=_j-1};
		
		if (_i <= _j) then {
			_k = 0;
			
			while "_k < count _arrays" do {
				_currentARR = _arrays select _k;
				_temp = _currentARR select _i;
				_currentARR set [_i, (_currentARR select _j)];
				_currentARR set [_j, _temp];
				_arrays set [_k, _currentARR];
				_k = _k + 1;
			};
			
			_i = _i + 1;
			_j = _j - 1;
		};
	};
	
	if ( _lo < _j )  then  { [_arrays, _lo, _j] call quicksortM };
	if ( _i < _hi )  then  { [_arrays, _i, _hi] call quicksortM };
	
	QUICKSORT_RECURRENCE  = QUICKSORT_RECURRENCE - 1;
	if (QUICKSORT_RECURRENCE == 0) then {QUICKSORT_RECURRENCE=nil};
};


// Compare arrays
FREVIVE_MATCH_ARRAY = {
	private ["_return", "_array1", "_array2", "_i"];
	_return = false;
	_array1 = _this select 0;
	_array2 = _this select 1;
	
	if (count _array1 == count _array2) then {
		_return = true;
		_i      = -1;
		
		while "_i=_i+1; _i<count _array1 && _return" do {
			if ((_array1 select _i) != (_array2 select _i)) then {
				_return = false;
			}
		}
	} else {
		_return = false
	};
	
	_return
};


// Kegetys' Spectating Script nextCam.sqs
FREVIVE_SPECTATOR_NEXTCAM = {
	private ["_tries", "_DeathCamIndex", "_alive", "_name"];
	
	if (count DeathCamArray!=0 && count DeathCamArrayID!=0) then {
		_tries         = 0;
		_DeathCamIndex = DeathCamIndex;
		_alive         = false;
		
		if (_this == 0) then {
			_alive = true;
		} else {
			while "!_alive && _tries<(count DeathCamArrayID)+1" do {
				_DeathCamIndex = _DeathCamIndex + _this;
				
				if (_DeathCamIndex < 0) then {_DeathCamIndex = count DeathCamArrayID-1};
				if (_DeathCamIndex >= count DeathCamArrayID) then {_DeathCamIndex = 0};
				
				if ((DeathCamArrayID select _DeathCamIndex) != -1) then {
					if (alive (DeathCamArray select (DeathCamArrayID select _DeathCamIndex))) then {
						_alive = true;
					} else {
						_tries = _tries + 1;
					};
				};
			};
		};

		if (_alive) then {
			DeathCamIndex = _DeathCamIndex;
			lbSetCurSel [1047002, DeathCamIndex];
			_name = name (DeathCamArray select (DeathCamArrayID select DeathCamIndex));
			if (_name == "error: no unit") then {_name = ""};
			ctrlSetText [116969,_name];
			DeathCamCurTarget = (DeathCamArray select (DeathCamArrayID select DeathCamIndex));
		};
	};
};


FREVIVE_HEIGHT_TO_ID = {
	private ["_height"]; 
	_height = (getPos _this select 2);

	if (_height < 10000) then {
		-1
	} else {
		(_height-(_height mod 1000))/1000-10
	}
};

FREVIVE_ID_TO_HEIGHT = {
	if (_this == -1) then {
		9999
	} else {
		(_this+10)*1000+999
	}
};

FREVIVE_SUSPEND = {
	if (local _this) then {
		_this setPos [(_location select _i) select 0,(_location select _i) select 1,(_reviving select _i) call FREVIVE_ID_TO_HEIGHT];
		_this setVelocity [0,0,0]; 
	};
};