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
    title: "DM码打印工具"
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
                text: backend ? backend.codeValue : ""
                placeholderText: "输入DM码内容"
                font.pixelSize: 14
                font.family: "Consolas, monospace"
                selectByMouse: true
                onTextChanged: { if (backend) backend.codeValue = text }
            }

            Label { text: "打印数量（张）"; font.pixelSize: 13; color: "#555" }
            SpinBox {
                id: batchSpin
                Layout.fillWidth: true
                from: 1
                to: 9999
                value: backend ? backend.batchCount : 1
                editable: true
                onValueChanged: { if (backend) backend.batchCount = value }
            }

            Button {
                Layout.fillWidth: true
                text: "生成预览"
                font.pixelSize: 14
                font.bold: true
                highlighted: true
                onClicked: { if (backend) backend.generatePreview() }

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
                model: backend ? backend.printerList : []
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

                    onClicked: { if (backend) backend.printLabels(printerCombo.currentText) }
                }

                Button {
                    Layout.fillWidth: true
                    text: "保存ZPL"
                    onClicked: { if (backend) backend.saveZpl(printerCombo.currentText, "dm_labels.zpl") }
                }
            }

            Item { Layout.fillHeight: true }
        }

        Rectangle {
            id: previewPanel
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "white"
            radius: 6
            border.color: "#DDD"
            border.width: 1

            readonly property real baseImageWidth: Math.max(240, width - 40)
            property real zoomFactor: 1.0
            readonly property real minZoom: 0.25
            readonly property real maxZoom: 2.5

            function clampZoom(v) {
                return Math.max(minZoom, Math.min(maxZoom, v))
            }

            // flick：预览 Flickable；viewX/viewY：相对其视口（与 contentX/Y 同坐标系）
            function applyZoomAt(flick, viewX, viewY, targetZoom) {
                var oldZoom = zoomFactor
                var newZoom = clampZoom(targetZoom)
                if (Math.abs(newZoom - oldZoom) < 0.0001) {
                    return
                }
                if (!flick) {
                    zoomFactor = newZoom
                    return
                }
                var sx = viewX + flick.contentX
                var sy = viewY + flick.contentY
                var ratio = newZoom / oldZoom
                zoomFactor = newZoom
                var maxX = Math.max(0, flick.contentWidth - flick.width)
                var maxY = Math.max(0, flick.contentHeight - flick.height)
                flick.contentX = Math.min(maxX, Math.max(0, sx * ratio - viewX))
                flick.contentY = Math.min(maxY, Math.max(0, sy * ratio - viewY))
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                Label {
                    Layout.fillWidth: true
                    text: "滚轮上下滚动预览；按住 Ctrl 再滚轮以鼠标位置为中心缩放（" +
                          Math.round(previewPanel.zoomFactor * 100) + "%）"
                    font.pixelSize: 12
                    color: "#666"
                }

                Flickable {
                    id: previewFlick
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    visible: backend && backend.previewImageUrls.length > 0

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }
                    ScrollBar.horizontal: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    contentWidth: previewContentRoot.width
                    contentHeight: previewContentRoot.height

                    Item {
                        id: previewContentRoot
                        width: Math.max(previewFlick.width, previewColumn.width)
                        height: previewColumn.height

                        Column {
                            id: previewColumn
                            spacing: 12
                            width: previewPanel.baseImageWidth *
                                   previewPanel.zoomFactor + 16
                            x: (parent.width - width) / 2

                            Repeater {
                                model: backend ? backend.previewImageUrls : []

                                Column {
                                    spacing: 4
                                    width: parent.width

                                    Label {
                                        text: "第 " + (index + 1) + " 张 "
                                        font.pixelSize: 12
                                        font.bold: true
                                        color: "#444"
                                    }

                                    Image {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        width: previewPanel.baseImageWidth *
                                               previewPanel.zoomFactor
                                        fillMode: Image.PreserveAspectFit
                                        source: modelData
                                        cache: false
                                        asynchronous: true
                                    }
                                }
                            }
                        }
                    }

                    // 作为 Flickable 子项：未 accept 的滚轮会交给 Flickable 默认滚动
                    MouseArea {
                        id: zoomMouseArea
                        anchors.fill: parent
                        acceptedButtons: Qt.NoButton
                        hoverEnabled: true
                        cursorShape: (
                            (zoomMouseArea.containsMouse && (Qt.application.keyboardModifiers & Qt.ControlModifier)) ?
                            Qt.SizeVerCursor : Qt.ArrowCursor
                        )

                        onWheel: function(wheel) {
                            if (!(wheel.modifiers & Qt.ControlModifier)) {
                                wheel.accepted = false
                                return
                            }
                            var step = wheel.angleDelta.y / 120.0
                            if (Math.abs(step) < 0.0001) {
                                wheel.accepted = false
                                return
                            }
                            var factor = Math.pow(1.12, step)
                            previewPanel.applyZoomAt(
                                previewFlick,
                                wheel.x,
                                wheel.y,
                                previewPanel.zoomFactor * factor
                            )
                            wheel.accepted = true
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    text: "点击「生成预览」按张数生成标签（最多预览 10 张）"
                    font.pixelSize: 15
                    color: "#AAA"
                    wrapMode: Text.WordWrap
                    visible: !backend || backend.previewImageUrls.length === 0
                }
            }
        }
    }

    footer: ToolBar {
        height: 32
        background: Rectangle { color: "#F0F0F0"; border.color: "#DDD"; border.width: 1 }
        Label {
            anchors.fill: parent
            anchors.leftMargin: 12
            text: backend ? backend.status : "初始化中..."
            font.pixelSize: 12
            color: "#666"
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }
}
