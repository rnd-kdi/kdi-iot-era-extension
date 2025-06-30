Blockly.Blocks["yolobit_mqtt_connect_wifi"] = {
  init: function () {
    this.jsonInit({
      colour: "#e65722",
      nextStatement: null,
      tooltip: "Kết nối vào mạng WiFi",
      message0: "Kết nối WiFi %1 %2 mật khẩu %3 %4",
      previousStatement: null,
      args0: [
        { type: "input_dummy" },
        { type: "input_value", name: "WIFI", check: "String" },
        { type: "input_dummy" },
        { type: "input_value", name: "PASSWORD", check: "String" },
      ],
      helpUrl: "",
    });
  },
};

Blockly.Blocks["yolobit_mqtt_connect_default_servers"] = {
  init: function () {
    this.jsonInit({
      colour: "#e65722",
      nextStatement: null,
      tooltip: "Kết nối đến server MQTT được chọn",
      message0: "Kết nối đến server %1 với Token %2 %3",
      previousStatement: null,
      args0: [
        {
          type: "field_dropdown",
          name: "SERVER",
          options: [
            ["ER-a", "mqtt1.eoh.io"]
          ],
        },
        { type: "input_value", name: "USERNAME", check: "String" }, // chỉ còn username (token)
        { type: "input_dummy" },
      ],
      helpUrl: "",
    });
  },
};


'use strict';

// Any imports need to be reserved words
Blockly.Python.addReservedWords('wifi');

Blockly.Python['yolobit_mqtt_connect_wifi'] = function(block) {
  Blockly.Python.definitions_['import_mqtt'] = 'from mqtt import *';
  var value_wifi = Blockly.Python.valueToCode(block, 'WIFI', Blockly.Python.ORDER_ATOMIC);
  var value_password = Blockly.Python.valueToCode(block, 'PASSWORD', Blockly.Python.ORDER_ATOMIC);
  // TODO: Assemble Python into code variable.
  var code = 'mqtt.connect_wifi(' + value_wifi + ', ' + value_password + ')\n';
  return code;
};

Blockly.Python['yolobit_mqtt_connect_default_servers'] = function(block) {
  Blockly.Python.definitions_['import_mqtt'] = 'from mqtt import *';
  var server   = block.getFieldValue('SERVER');
  var username = Blockly.Python.valueToCode(block, 'USERNAME', Blockly.Python.ORDER_ATOMIC);

  // TOKEN lấy từ username (token)
  Blockly.Python.definitions_['mqtt_token'] = 'TOKEN = ' + username;

  // Dùng username làm password luôn
  var code  = `mqtt.connect_broker(server='${server}', username=${username}, password=${username})\n`;
      code += 'time.sleep(2)\n';
  return code;
};


// 1) Định nghĩa block (không đổi)
Blockly.Blocks['yolobit_mqtt_subscribe_config_down'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Cập nhật thông tin từ server");
    this.setPreviousStatement(true);
    this.setNextStatement(true);
    this.setColour(230);
    this.setTooltip("Subscribe eoh/chip/{TOKEN}/config/down rồi in từng pin và config_id");
    this.setHelpUrl("");
  }
};

// 2) Generator Python (mới)
Blockly.Python['yolobit_mqtt_subscribe_config_down'] = function(block) {
  // đảm bảo có import mqtt và biến TOKEN
  Blockly.Python.definitions_['import_mqtt'] = 'from mqtt import *';
  Blockly.Python.definitions_['mqtt_token'] = Blockly.Python.definitions_['mqtt_token'] || '';
  var code  = 'mqtt.subscribe_config_down(TOKEN)\n';
      // code += 'for pin, cfg in mqtt.virtual_pins.items():\n';
      // code += '    print("Virtual pin V%d → config_id %d" % (pin, cfg))\n';
  return code;
};

// 3) (New) Publish value block
Blockly.Blocks['yolobit_mqtt_publish_value'] = {
  init: function() {
    this.appendValueInput('VALUE')
        .setCheck(['Number','String'])
        .appendField('Gửi giá trị');
    this.appendDummyInput()
        .appendField('lên kênh')
        .appendField(new Blockly.FieldDropdown([
          ['V0','0'], ['V1','1'], ['V2','2'], ['V3','3'],
          ['V4','4'], ['V5','5'], ['V6','6'], ['V7','7'],
          ['V8','8'], ['V9','9']
        ]), 'PIN');
    this.setPreviousStatement(true);
    this.setNextStatement(true);
    this.setColour(230);
    this.setTooltip('Gửi giá trị NUMBER lên Virtual pin Vn');
    this.setHelpUrl('');
  }
};

Blockly.Python['yolobit_mqtt_publish_value'] = function(block) {
  // đảm bảo đã import mqtt
  Blockly.Python.definitions_['import_mqtt'] = 'from mqtt import *';
  var valueCode = Blockly.Python.valueToCode(block, 'VALUE', Blockly.Python.ORDER_ATOMIC) || '0';
  var pin = block.getFieldValue('PIN');
  // gọi method virtual_write(pin, value, username)
  var code = `mqtt.virtual_write(${pin}, ${valueCode}, username=TOKEN)\n`;
  return code;
};

// Thêm vào definition.js

// Block để subscribe virtual pin
// Blockly.Blocks['yolobit_mqtt_subscribe_virtual_pin'] = {
//   init: function() {
//     this.appendDummyInput()
//         .appendField('theo dõi Virtual pin')
//         .appendField(new Blockly.FieldDropdown([
//           ['V0','0'], ['V1','1'], ['V2','2'], ['V3','3'],
//           ['V4','4'], ['V5','5'], ['V6','6'], ['V7','7'],
//           ['V8','8'], ['V9','9']
//         ]), 'PIN');
//     this.setPreviousStatement(true);
//     this.setNextStatement(true);
//     this.setColour(230);
//     this.setTooltip('Subscribe và theo dõi dữ liệu từ Virtual pin');
//     this.setHelpUrl('');
//   }
// };

// // Generator Python cho subscribe virtual pin
// Blockly.Python['yolobit_mqtt_subscribe_virtual_pin'] = function(block) {
//   Blockly.Python.definitions_['import_mqtt'] = 'from mqtt import *';
//   var pin = block.getFieldValue('PIN');
//   var code = `mqtt.subscribe_virtual_pin(${pin}, TOKEN)\n`;
//   return code;
// };

// Block để đọc giá trị từ virtual pin
Blockly.Blocks['yolobit_mqtt_read_virtual_pin_value'] = {
  init: function() {
    this.appendDummyInput()
        .appendField('Giá trị từ kênh')
        .appendField(new Blockly.FieldDropdown([
          ['V0','0'], ['V1','1'], ['V2','2'], ['V3','3'],
          ['V4','4'], ['V5','5'], ['V6','6'], ['V7','7'],
          ['V8','8'], ['V9','9']
        ]), 'PIN');
    this.setOutput(true, 'Number');
    this.setColour(230);
    this.setTooltip('Lấy giá trị mới nhất từ Virtual pin');
    this.setHelpUrl('');
  }
};

// Generator Python cho đọc giá trị virtual pin
Blockly.Python['yolobit_mqtt_read_virtual_pin_value'] = function(block) {
  Blockly.Python.definitions_['import_mqtt'] = 'from mqtt import *';
  var pin = block.getFieldValue('PIN');
  var code = `mqtt.subscribe_and_get(${pin}, TOKEN)`;
  return [code, Blockly.Python.ORDER_FUNCTION_CALL];
};

// // Block để đọc đầy đủ thông tin từ virtual pin (bao gồm trigger_id)
// Blockly.Blocks['yolobit_mqtt_read_virtual_pin_full'] = {
//   init: function() {
//     this.appendDummyInput()
//         .appendField('thông tin đầy đủ từ V')
//         .appendField(new Blockly.FieldDropdown([
//           ['V0','0'], ['V1','1'], ['V2','2'], ['V3','3'],
//           ['V4','4'], ['V5','5'], ['V6','6'], ['V7','7'],
//           ['V8','8'], ['V9','9']
//         ]), 'PIN');
//     this.setOutput(true, null);
//     this.setColour(230);
//     this.setTooltip('Lấy thông tin đầy đủ (value, trigger_id, timestamp) từ Virtual pin');
//     this.setHelpUrl('');
//   }
// };

// // Generator Python cho đọc thông tin đầy đủ
// Blockly.Python['yolobit_mqtt_read_virtual_pin_full'] = function(block) {
//   Blockly.Python.definitions_['import_mqtt'] = 'from mqtt import *';
//   var pin = block.getFieldValue('PIN');
//   var code = `mqtt.get_virtual_pin_value(${pin})`;
//   return [code, Blockly.Python.ORDER_FUNCTION_CALL];
// };