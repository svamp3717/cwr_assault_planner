// WW4 Arsenal: family, variant, compatible item

class WW4_Arsenal_RscText
{
    type = 0;
    idc = -1;
    style = 0;
    colorBackground[] = {0,0,0,0};
    colorText[] = {1,1,1,1};
    font = "TahomaB";
    sizeEx = 0.025;
    text = "";
};

class WW4_Arsenal_RscButton
{
    type = 1;
    idc = -1;
    style = 2;
    colorText[] = {1,1,1,1};
    colorDisabled[] = {0.4,0.4,0.4,1};
    colorBackground[] = {0.15,0.15,0.15,1};
    colorBackgroundActive[] = {0.3,0.3,0.3,1};
    colorBackgroundDisabled[] = {0.1,0.1,0.1,0.5};
    colorFocused[] = {0.25,0.25,0.25,1};
    colorShadow[] = {0,0,0,0};
    colorBorder[] = {0,0,0,1};
    soundEnter[] = {"",0.1,1};
    soundPush[] = {"",0.1,1};
    soundClick[] = {"",0.1,1};
    soundEscape[] = {"",0.1,1};
    font = "TahomaB";
    sizeEx = 0.023;
    offsetX = 0.003;
    offsetY = 0.003;
    offsetPressedX = 0.002;
    offsetPressedY = 0.002;
    borderSize = 0;
    text = "";
    action = "";
};

class WW4_Arsenal_RscListBox
{
    type = 5;
    idc = -1;
    style = 0;
    font = "TahomaB";
    sizeEx = 0.021;
    rowHeight = 0.03;
    colorText[] = {1,1,1,1};
    colorSelect[] = {1,1,1,1};
    colorSelect2[] = {1,1,1,1};
    colorSelectBackground[] = {0.05,0.05,0.05,0.95};
    colorSelectBackground2[] = {0.05,0.05,0.05,0.95};
    colorBackground[] = {0.05,0.05,0.05,0.95};
    colorScrollbar[] = {1,1,1,1};
    soundSelect[] = {"",0.1,1};
    period = 1;
};

class WW4_Arsenal_Dialog
{
    idd = 8800;
    movingEnable = 1;
    controlsBackground[] = {WW4_Background,WW4_Title};
    objects[] = {};
    controls[] = {
        WW4_FamilyLabel,WW4_FamilyList,
        WW4_VariantLabel,WW4_VariantList,
        WW4_AmmoLabel,WW4_AmmoList,
        WW4_Status,
        WW4_AddWeapon,WW4_AddOne,WW4_AddFive,
        WW4_Apply,WW4_Spectate,WW4_Clear,WW4_PlayerModelButton,WW4_Close
    };

    class WW4_Background: WW4_Arsenal_RscText
    {
        x = 0.025; y = 0.04; w = 0.95; h = 0.92;
        colorBackground[] = {0,0,0,0.88};
    };
    class WW4_Title: WW4_Arsenal_RscText
    {
        idc = 1000;
        x = 0.025; y = 0.04; w = 0.95; h = 0.055;
        style = 2;
        moving = 1;
        sizeEx = 0.034;
        colorBackground[] = {0.18,0.22,0.18,1};
        text = "WW4 ARSENAL";
    };
    class WW4_FamilyLabel: WW4_Arsenal_RscText
    {
        x = 0.045; y = 0.11; w = 0.24; h = 0.04;
        colorText[] = {0.20,1.00,0.20,1};
        colorBackground[] = {0.08,0.16,0.08,1};
        text = "Weapon / equipment family";
    };
    class WW4_FamilyList: WW4_Arsenal_RscListBox
    {
        idc = 1500;
        x = 0.045; y = 0.15; w = 0.24; h = 0.59;
        colorSelect[] = {0.20,1.00,0.20,1};
        colorSelect2[] = {0.20,1.00,0.20,1};
        colorSelectBackground[] = {0.05,0.05,0.05,0.95};
        colorSelectBackground2[] = {0.05,0.05,0.05,0.95};
    };
    class WW4_VariantLabel: WW4_Arsenal_RscText
    {
        x = 0.305; y = 0.11; w = 0.31; h = 0.04;
        colorText[] = {0.25,0.65,1.00,1};
        colorBackground[] = {0.06,0.10,0.18,1};
        text = "Variant";
    };
    class WW4_VariantList: WW4_Arsenal_RscListBox
    {
        idc = 1501;
        x = 0.305; y = 0.15; w = 0.31; h = 0.59;
        colorSelect[] = {0.25,0.65,1.00,1};
        colorSelect2[] = {0.25,0.65,1.00,1};
        colorSelectBackground[] = {0.05,0.05,0.05,0.95};
        colorSelectBackground2[] = {0.05,0.05,0.05,0.95};
    };
    class WW4_AmmoLabel: WW4_Arsenal_RscText
    {
        x = 0.635; y = 0.11; w = 0.32; h = 0.04;
        colorText[] = {1.00,0.65,0.10,1};
        colorBackground[] = {0.18,0.11,0.03,1};
        text = "Compatible magazine / item";
    };
    class WW4_AmmoList: WW4_Arsenal_RscListBox
    {
        idc = 1502;
        x = 0.635; y = 0.15; w = 0.32; h = 0.59;
        colorSelect[] = {1.00,0.65,0.10,1};
        colorSelect2[] = {1.00,0.65,0.10,1};
        colorSelectBackground[] = {0.05,0.05,0.05,0.95};
        colorSelectBackground2[] = {0.05,0.05,0.05,0.95};
    };
    class WW4_Status: WW4_Arsenal_RscText
    {
        idc = 1002;
        x = 0.045; y = 0.755; w = 0.91; h = 0.035;
        sizeEx = 0.020;
        text = "Select a family and variant.";
    };
    class WW4_AddWeapon: WW4_Arsenal_RscButton
    {
        x = 0.045; y = 0.805; w = 0.135; h = 0.055;
        text = "Add weapon/item";
        action = "[] exec ""ww4_arsenal\add_weapon.sqs""";
    };
    class WW4_AddOne: WW4_Arsenal_RscButton
    {
        x = 0.190; y = 0.805; w = 0.135; h = 0.055;
        text = "Add 1";
        action = "[] exec ""ww4_arsenal\add_magazine.sqs""";
    };
    class WW4_AddFive: WW4_Arsenal_RscButton
    {
        x = 0.335; y = 0.805; w = 0.135; h = 0.055;
        text = "Add 5";
        action = "[] exec ""ww4_arsenal\add_five_magazines.sqs""";
    };
    class WW4_Apply: WW4_Arsenal_RscButton
    {
        x = 0.480; y = 0.805; w = 0.145; h = 0.055;
        text = "Apply";
        action = "[] exec ""ww4_arsenal\apply_loadout.sqs""";
    };

    class WW4_Spectate: WW4_Arsenal_RscButton
    {
        x = 0.635; y = 0.805; w = 0.155; h = 0.055;
        text = "Spectate";
        colorBackground[] = {0.30,0.16,0.42,1};
        colorBackgroundActive[] = {0.48,0.28,0.64,1};
        action = "[] exec ""ww4_arsenal\preview_weapon.sqs""";
    };
    class WW4_Clear: WW4_Arsenal_RscButton
    {
        x = 0.800; y = 0.805; w = 0.155; h = 0.055;
        text = "Clear gear";
        action = "[] exec ""ww4_arsenal\clear_gear.sqs""";
    };
    class WW4_PlayerModelButton: WW4_Arsenal_RscButton
    {
        x = 0.255; y = 0.885; w = 0.23; h = 0.05;
        text = "Player model (SP only)";
        colorBackground[] = {0.08,0.32,0.34,1};
        colorBackgroundActive[] = {0.12,0.52,0.55,1};
        action = "[] exec ""ww4_arsenal\to_models.sqs""";
    };

    class WW4_Close: WW4_Arsenal_RscButton
    {
        x = 0.515; y = 0.885; w = 0.23; h = 0.05;
        text = "Close";
        action = "closeDialog 0";
    };
};

class WW4_Preview_AbortDialog
{
    idd = 8801;
    movingEnable = 0;
    controlsBackground[] = {};
    objects[] = {};
    controls[] = {WW4_AbortMessage,WW4_AbortClickArea};

    class WW4_AbortMessage: WW4_Arsenal_RscText
    {
        idc = -1;
        x = 0.20;
        y = 0.88;
        w = 0.60;
        h = 0.055;
        style = 2;
        sizeEx = 0.026;
        colorText[] = {1,1,1,1};
        colorBackground[] = {0,0,0,0.65};
        text = "CLICK ANYWHERE TO ABORT WEAPON PREVIEW";
    };

    class WW4_AbortClickArea: WW4_Arsenal_RscButton
    {
        idc = 1600;
        x = 0;
        y = 0;
        w = 1;
        h = 1;
        text = "";
        action = "WW4_PreviewAbort = true";

        colorText[] = {0,0,0,0};
        colorDisabled[] = {0,0,0,0};
        colorBackground[] = {0,0,0,0.001};
        colorBackgroundActive[] = {0,0,0,0.001};
        colorBackgroundDisabled[] = {0,0,0,0};
        colorFocused[] = {0,0,0,0.001};
        colorShadow[] = {0,0,0,0};
        colorBorder[] = {0,0,0,0};

        soundEnter[] = {"",0,1};
        soundPush[] = {"",0,1};
        soundClick[] = {"",0,1};
        soundEscape[] = {"",0,1};
        borderSize = 0;
    };
};

class WW4_PlayerModel_Dialog
{
    idd = 8802;
    movingEnable = 1;
    controlsBackground[] = {WW4_ModelBackground,WW4_ModelTitle};
    objects[] = {};
    controls[] = {
        WW4_ModelCategoryLabel,
        WW4_ModelCategoryList,
        WW4_ModelClassLabel,
        WW4_ModelClassList,
        WW4_ModelStatus,
        WW4_ModelApply,
        WW4_ModelPreview,
        WW4_ModelBack,
        WW4_ModelClose
    };

    class WW4_ModelBackground: WW4_Arsenal_RscText
    {
        x = 0.10;
        y = 0.08;
        w = 0.80;
        h = 0.84;
        colorBackground[] = {0,0,0,0.90};
    };

    class WW4_ModelTitle: WW4_Arsenal_RscText
    {
        x = 0.10;
        y = 0.08;
        w = 0.80;
        h = 0.06;
        style = 2;
        moving = 1;
        sizeEx = 0.034;
        colorBackground[] = {0.08,0.32,0.34,1};
        text = "WW4 PLAYER MODEL";
    };

    class WW4_ModelCategoryLabel: WW4_Arsenal_RscText
    {
        x = 0.13;
        y = 0.16;
        w = 0.29;
        h = 0.04;
        colorText[] = {0.20,1.00,0.85,1};
        colorBackground[] = {0.04,0.16,0.14,1};
        text = "West category";
    };

    class WW4_ModelCategoryList: WW4_Arsenal_RscListBox
    {
        idc = 1510;
        x = 0.13;
        y = 0.20;
        w = 0.29;
        h = 0.54;
        colorSelect[] = {0.20,1.00,0.85,1};
        colorSelect2[] = {0.20,1.00,0.85,1};
        colorSelectBackground[] = {0.05,0.05,0.05,0.95};
        colorSelectBackground2[] = {0.05,0.05,0.05,0.95};
    };

    class WW4_ModelClassLabel: WW4_Arsenal_RscText
    {
        x = 0.45;
        y = 0.16;
        w = 0.42;
        h = 0.04;
        colorText[] = {1.00,0.42,0.82,1};
        colorBackground[] = {0.18,0.05,0.14,1};
        text = "Player model classname";
    };

    class WW4_ModelClassList: WW4_Arsenal_RscListBox
    {
        idc = 1511;
        x = 0.45;
        y = 0.20;
        w = 0.42;
        h = 0.54;
        colorSelect[] = {1.00,0.42,0.82,1};
        colorSelect2[] = {1.00,0.42,0.82,1};
        colorSelectBackground[] = {0.05,0.05,0.05,0.95};
        colorSelectBackground2[] = {0.05,0.05,0.05,0.95};
    };

    class WW4_ModelStatus: WW4_Arsenal_RscText
    {
        idc = 1010;
        x = 0.13;
        y = 0.755;
        w = 0.74;
        h = 0.045;
        style = 2;
        sizeEx = 0.021;
        text = "Apply uses the backported selectPlayer command. Preview is visual only.";
    };

    class WW4_ModelApply: WW4_Arsenal_RscButton
    {
        x = 0.13;
        y = 0.825;
        w = 0.18;
        h = 0.055;
        text = "Apply model (test)";
        colorBackground[] = {0.34,0.10,0.27,1};
        colorBackgroundActive[] = {0.56,0.16,0.44,1};
        action = "[] exec ""ww4_arsenal\apply_player_model.sqs""";
    };

    class WW4_ModelPreview: WW4_Arsenal_RscButton
    {
        x = 0.32;
        y = 0.825;
        w = 0.16;
        h = 0.055;
        text = "Preview";
        colorBackground[] = {0.25,0.16,0.40,1};
        colorBackgroundActive[] = {0.42,0.28,0.62,1};
        action = "[] exec ""ww4_arsenal\preview_player_model.sqs""";
    };

    class WW4_ModelBack: WW4_Arsenal_RscButton
    {
        x = 0.49;
        y = 0.825;
        w = 0.20;
        h = 0.055;
        text = "Back to arsenal";
        action = "[] exec ""ww4_arsenal\to_arsenal.sqs""";
    };

    class WW4_ModelClose: WW4_Arsenal_RscButton
    {
        x = 0.70;
        y = 0.825;
        w = 0.17;
        h = 0.055;
        text = "Close";
        action = "closeDialog 0";
    };
};

