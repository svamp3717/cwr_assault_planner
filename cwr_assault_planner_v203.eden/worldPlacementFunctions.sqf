// CWA/OFP placement helpers, loaded after worldConfig.sqs on every machine.
// [x,y,z,margin] -> bounded position; cap margin to half the shorter axis.
worldClampPosition = {
    private ["_x","_y","_z","_margin","_halfX","_halfY"];
    _x = _this select 0;
    _y = _this select 1;
    _z = _this select 2;
    _margin = _this select 3;
    _halfX = (worldMaxX - worldMinX) / 2;
    _halfY = (worldMaxY - worldMinY) / 2;
    if (_margin > _halfX) then {_margin = _halfX};
    if (_margin > _halfY) then {_margin = _halfY};
    if (_x < worldMinX + _margin) then {_x = worldMinX + _margin};
    if (_x > worldMaxX - _margin) then {_x = worldMaxX - _margin};
    if (_y < worldMinY + _margin) then {_y = worldMinY + _margin};
    if (_y > worldMaxY - _margin) then {_y = worldMaxY - _margin};
    [_x,_y,_z]
};

// [x,y,dx,dy,z,margin] -> offset, reflecting an axis only when it improves
// available distance and the requested point would be clipped.
worldOffsetPosition = {
    private ["_x","_y","_dx","_dy","_z","_margin","_pos","_alt"];
    _x = _this select 0;
    _y = _this select 1;
    _dx = _this select 2;
    _dy = _this select 3;
    _z = _this select 4;
    _margin = _this select 5;
    _pos = [_x + _dx,_y + _dy,_z,_margin] call worldClampPosition;
    _alt = [_x - _dx,_y - _dy,_z,_margin] call worldClampPosition;
    if (abs ((_pos select 0) - _x) < abs ((_alt select 0) - _x)) then {_dx = -_dx};
    if (abs ((_pos select 1) - _y) < abs ((_alt select 1) - _y)) then {_dy = -_dy};
    [_x + _dx,_y + _dy,_z,_margin] call worldClampPosition
};

// [dx,dy,z] relative to setup base. Fit the legacy layout as a whole,
// preserving spacing instead of stacking all units on a map boundary.
worldSetupPosition = {
    private ["_dx","_dy","_z","_scale","_scaleX","_scaleY","_ax","_ay"];
    _dx = _this select 0;
    _dy = _this select 1;
    _z = _this select 2;
    _scale = 1;
    _scaleX = (worldMaxX - worldMinX) / 640;
    _scaleY = (worldMaxY - worldMinY) / 850;
    if (_scale > _scaleX) then {_scale = _scaleX};
    if (_scale > _scaleY) then {_scale = _scaleY};
    _ax = missionBaseX;
    _ay = missionBaseY;
    if (_ax < worldMinX + 150 * _scale) then {_ax = worldMinX + 150 * _scale};
    if (_ax > worldMaxX - 490 * _scale) then {_ax = worldMaxX - 490 * _scale};
    if (_ay < worldMinY + 810 * _scale) then {_ay = worldMinY + 810 * _scale};
    if (_ay > worldMaxY - 40 * _scale) then {_ay = worldMaxY - 40 * _scale};
    [_ax + _dx * _scale,_ay + _dy * _scale,_z]
};

// [x,y,z] -> position lies inside the configured playable rectangle.
worldPositionInBounds = {
    ((_this select 0) >= worldMinX) && ((_this select 0) <= worldMaxX) && ((_this select 1) >= worldMinY) && ((_this select 1) <= worldMaxY)
};

// Town index -> numeric world position; legacy markers only when requested.
// Missing legacy markers often return [0,0,0]; retain the numeric position.
worldTownPosition = {
    private ["_i","_pos","_legacy"];
    _i = _this;
    _pos = [missionTownXs select _i, missionTownYs select _i, 0];
    if (worldUseEditorLocationMarkers) then {
        _legacy = getMarkerPos (missionTownMarkers select _i);
        if (((_legacy select 0) != 0 || (_legacy select 1) != 0) && (_legacy call worldPositionInBounds)) then {_pos = _legacy};
    };
    _pos
};

// Use actual coordinates rather than labels: names need not be unique.
worldPositionIsObjective = {
    private ["_pos","_xs","_ys","_i","_dx","_dy","_blocked"];
    _pos = _this;
    _xs = [primaryX,secondaryX,thirdX,fourthX,fifthX];
    _ys = [primaryY,secondaryY,thirdY,fourthY,fifthY];
    _i = 0;
    _blocked = false;
    {
        if (_i < townCount) then {
            _dx = (_pos select 0) - _x;
            _dy = (_pos select 1) - (_ys select _i);
            if ((_dx * _dx + _dy * _dy) <= 1) then {_blocked = true};
        };
        _i = _i + 1;
    } forEach _xs;
    _blocked
};

// [sourceX,sourceY,minDistance,maxDistance,excludedIndices] -> nearest
// non-objective town index, or -1. Negative maxDistance means unlimited.
worldNearestTown = {
    private ["_sx","_sy","_min","_max","_excluded","_i","_pos","_dx","_dy","_dist","_best","_bestDist"];
    _sx = _this select 0;
    _sy = _this select 1;
    _min = _this select 2;
    _max = _this select 3;
    _excluded = _this select 4;
    _i = 0;
    _best = -1;
    _bestDist = 0;
    {
        if (!(_i in _excluded)) then {
            _pos = _i call worldTownPosition;
            if ((_pos call worldPositionInBounds) && !(_pos call worldPositionIsObjective)) then {
                _dx = (_pos select 0) - _sx;
                _dy = (_pos select 1) - _sy;
                _dist = _dx * _dx + _dy * _dy;
                if (_dist >= _min * _min && (_max < 0 || _dist <= _max * _max) && (_best < 0 || _dist < _bestDist)) then {
                    _best = _i;
                    _bestDist = _dist;
                };
            };
        };
        _i = _i + 1;
    } forEach missionTownLabels;
    _best
};

// [sourceX,sourceY] -> safe settlement index. Prefer 500 m, but allow
// 250 m on small terrains. Never select an objective or the map origin
// simply because no valid settlement exists.
worldFindEscortTown = {
    private ["_sx","_sy","_index"];
    _sx = _this select 0;
    _sy = _this select 1;
    _index = [_sx,_sy,500,-1,[]] call worldNearestTown;
    if (_index < 0) then {_index = [_sx,_sy,250,-1,[]] call worldNearestTown};
    _index
};
