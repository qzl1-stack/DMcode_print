import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 900
    height: 680
    minimumWidth: 780
    minimumHeight: 580
    visible: true
    title: "DM码打印工具 v2.0"
    color: "#F5F5F5"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        ColumnLayout {
            Layout.preferredWidth: 240
            Layout.maximumWidth: 280
            Layout.fillHeight: true
            spacing: 12

            Label {
                text: "DM码打印工具"
                font.pixelSize: 18
                font.bold: true
                color: "#333"
            }

            Rectangle { height: 1; Layout.fillWidth: true; color: "#DDD" }

            Label { text: "码值"; font.pixelSize: 13; color: "#555" }
            TextField {
                id: codeInput
                Layout.fillWidth: true
                text: backend.codeValue
                placeholderText: "输入DM码内容"
                font.pixelSize: 14
                font.family: "Consolas, monospace"
                selectByMouse: true
                onTextChanged: backend.codeValue = text
            }

            Label { text: "打印数量（张）"; font.pixelSize: 13; color: "#555" }
            SpinBox {
                id: batchSpin
                Layout.fillWidth: true
                from: 1
                to: 9999
                value: backend.batchCount
                editable: true
                onValueChanged: backend.batchCount = value
            }

            Button {
                Layout.fillWidth: true
                text: "生成预览"
                font.pixelSize: 14
                font.bold: true
                highlighted: true
                onClicked: backend.generatePreview()

                background: Rectangle {
                    color: parent.pressed ? "#005A9E" : (parent.hovered ? "#106EBE" : "#0078D4")
                    radius: 4
                }
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }

            Rectangle { height: 1; Layout.fillWidth: true; color: "#DDD" }

            Label { text: "打印机"; font.pixelSize: 13; color: "#555" }
            ComboBox {
                id: printerCombo
                Layout.fillWidth: true
                model: backend.printerList
                editable: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Button {
                    Layout.fillWidth: true
                    text: "打印"
                    font.bold: true

                    background: Rectangle {
                        color: parent.pressed ? "#0B5A0B" : (parent.hovered ? "#0E6B0E" : "#107C10")
                        radius: 4
                    }
                    contentItem: Text {
                        text: parent.text
                        font: parent.font
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    onClicked: backend.printLabels(printerCombo.currentText)
                }

                Button {
                    Layout.fillWidth: true
                    text: "保存ZPL"
                    onClicked: backend.saveZpl(printerCombo.currentText, "dm_labels.zpl")
                }
            }

            Item { Layout.fillHeight: true }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "white"
            radius: 6
            border.color: "#DDD"
            border.width: 1

            Image {
                id: previewImage
                anchors.fill: parent
                anchors.margins: 8
                fillMode: Image.PreserveAspectFit
                source: backend.previewUrl
                cache: false
                asynchronous: false

                onStatusChanged: {
                    if (status === Image.Error) {
                        placeholderText.visible = true
                    } else if (status === Image.Ready) {
                        placeholderText.visible = false
                    }
                }
            }

            Text {
                id: placeholderText
                anchors.centerIn: parent
                text: "点击「生成预览」查看标签效果"
                font.pixelSize: 16
                color: "#AAA"
                visible: backend.previewUrl === ""
            }
        }
    }

    footer: ToolBar {
        height: 32
        background: Rectangle { color: "#F0F0F0"; border.color: "#DDD"; border.width: 1 }
        Label {
            anchors.fill: parent
            anchors.leftMargin: 12
            text: backend.status
            font.pixelSize: 12
            color: "#666"
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }
}
