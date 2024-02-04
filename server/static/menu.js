function talkmenu(operate, menuitemid, msg) {
    $.ajax({
        url: '/menu',
        type: "POST",
        data: { "type": operate, "menuitemid": menuitemid, 'validate': getCookie('validation') },
        success: function (res) {
            var data = JSON.parse(res);
            if (!msg) msg = '';
            if (data.code == 0) {
                toastr.success(msg + '成功');
            } else {
                toastr.error(data.message, msg + '失败');
            }
        },
        error: function () {
            toastr.error('服务器异常', msg + '失败');
        }
    });
}
//保存编辑窗体的原始值
var jsonTextInit = '';
var selectItemID = -1;

jQuery.fn.disable = function () {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function (opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

//定义列定义
columns = [
    { radio: true },
    {
        field: 'ENABLE', title: '状态', sortable: true, width: '50', align: 'center'
        , formatter: function (val, row, index) {
            if (val == 1)
                return "启用";
            else
                return "禁用";
        }
    },
    { field: 'ORDERNO', title: '顺序', sortable: true, width: '50', align: 'center' },
    { field: 'NAME', title: '名称', sortable: true, width: '250', align: 'left' },
    { field: 'OPENEVENT', title: '打开事件', sortable: true, width: '50', align: 'center' },
    { field: 'CLOSEEVENT', title: '关闭事件', sortable: true, width: '50', align: 'center' },
    { field: 'SLEEP', title: '等待(秒)', sortable: true, width: '50', align: 'center' },
    { field: 'DESC', title: '演讲词', visible: false },
    { field: 'ID', title: '操作', width: '350', align: 'center', valign: 'middle', formatter: actionFormatter }
];
//操作栏的格式化
function actionFormatter(value, row, index) {
    var id = value;
    var result = "";
    if (row.ENABLE == 1) {
        result += "<a href='javascript:;' class='btn btn-info mb-2' style='margin:5px' onclick=\"SwitchEnableStatus(" + id + "," + row["ENABLE"] + ",'禁用')\" title='禁用后不演示该节点'>";
        result += "<span class='fas fa-warning'></span>禁用</a>";
    }
    else {
        result += "<a href='javascript:;' class='btn btn-info mb-2' style='margin:5px' onclick=\"SwitchEnableStatus(" + id + "," + row["ENABLE"] + ",'启用')\" title='启用该节目'>";
        result += "<span class='fas fa-success'></span>启用</a>";
    }
    result += "<a href='javascript:;' class='btn btn-primary mb-2' style='margin:5px' onclick=\"EditViewById(" + id + ")\" title='编辑演讲内容'>";
    result += "<span class='fas fa-edit'></span>编辑</a>";
    result += "<a href='javascript:;' class='btn btn-danger mb-2' style='margin:5px' onclick=\"DeleteById(" + id + ")\" title='删除后不能恢复'>";
    result += "<span class='fas fa-trash'></span>删除</a>";
    result += "<a href='javascript:;' class='btn btn-success mb-2' style='margin:5px' onclick=\"PlayById(" + id + ")\" title='播放该节点演讲内容'>";
    result += "<span class='fas fa-play'></span>播放</a>";
    return result;
}
//
function SwitchEnableStatus(id, enablestatus, msg) {
    if (enablestatus == 1)
        enablestatus = 0
    else
        enablestatus = 1

    $.ajax({
        url: '/menu',
        type: "PUT",
        data: { "id": id, "enable": enablestatus, 'validate': getCookie('validation') },
        success: function (res) {
            var data = JSON.parse(res);
            if (!msg) msg = '';
            if (data.code == 0) {
                //更新记录
                $('#menuItemsTable').bootstrapTable('updateByUniqueId', {
                    id: id, row: {
                        "ENABLE": enablestatus
                    }
                });
                toastr.success(msg + '成功');
               
            } else {
                toastr.error(data.message, msg + '失败');
            }
        },
        error: function () {
            toastr.error('服务器异常', '获取节点数据失败');
        }
    });
}
//播放节点
function PlayById(id) {
    selectItemID = id;
    talkmenu(1, selectItemID, '播放')
}
//停止播放
function StopPlay() {
    talkmenu(4, selectItemID, '停止')
}
//删除节点
function DeleteById(id) {
    selectItemID = id;
    //弹出删除模态框
    $('#deleteModal').modal('show')
}
//调用编辑窗体
function EditViewById(id) {
    selectItemID = id;
    $.ajax({
        url: '/menuitems',
        type: "GET",
        data: { "menuid": id, 'validate': getCookie('validation') },
        success: function (res) {
            var data_json = JSON.parse(res);
            if (data_json.length > 0) {
                // $("#itemid").val(data_json[0].ID);
                $("#itemname").val(data_json[0].NAME);
                $("#itemorderno").val(data_json[0].ORDERNO);
                $("#itemsleep").val(data_json[0].SLEEP);
                $("#itemdesc").text(data_json[0].DESC);
                $("#itemopenevent").val(data_json[0].OPENEVENT);
                $("#itemcloseevent").val(data_json[0].CLOSEEVENT);
                //弹出修改模态框，非新增模态框
                $('#editModal').modal('show')
                // 暂存未修改时数据
                var dataformInit = $("#form_edit").serializeArray();
                jsonTextInit = JSON.stringify({ dataform: dataformInit });
            }
            else {
                toastr.error('找不到记录', '获取节点数据失败');
            }
        },
        error: function () {
            toastr.error('服务器异常', '获取节点数据失败');
        }
    });

}
//调用新增窗体
function AddMenu() {
    selectItemID = -1;
    //弹出修改模态框，新增模态框
    $('#editModal').modal('show')
    // 暂存未修改时数据
    var dataformInit = $("#form_edit").serializeArray();
    jsonTextInit = JSON.stringify({ dataform: dataformInit });
}
//初始化列表
function InitmenuItemsTable() {
    $('#menuItemsTable').bootstrapTable({
        url: '/menuitems',
        method: 'get',
        columns: columns,
        uniqueId: 'ID',
        resizable: true,
        pagination: true,
        sidePagination: 'client',
        clickToSelect: true,
        maintainSelected: true,
        striped: true,                      //是否显示行间隔色
        sortable: true,                     //是否启用排序
        sortOrder: 'asc',                   //排序方式
        singleSelect: true,             //单选
        pageNumber: 1,
        pageSize: 10,
        pageList: [10, 20, 30],
        search: true,
        showRefresh: true,
        showToggle: true,
        showColumns: true,
        queryParams: function (params) {
            var param = {
                validate: getCookie('validation')
            };
            return param;
        },
        onPostBody: function (data) {
            if (selectItemID > 0) {
                $('#menuItemsTable').bootstrapTable('checkBy', { field: 'ID', values: [selectItemID] });
            }
        }
    });
};

$(function () {

    //初始化节目表
    InitmenuItemsTable();
    //关闭编辑窗体后清空
    $('#editModal').on('hidden.bs.modal', function () {
        // 清空表单
        $('#form_edit')[0].reset();
        $("#itemname").val("");
        $("#itemorderno").val("0");
        $("#itemsleep").val("0");
        $("#itemsopenevent").val("-1");
        $("#itemscloseevent").val("-1");
        $("#itemdesc").text("");
    });
    //提交节点保存
    $("#but_submit_add").click(function () {
        // 判断是否修改
        var dataform = $("#form_edit").serializeArray();
        var jsonText = JSON.stringify({ dataform: dataform });
        if (jsonText == jsonTextInit) {
            $("#editModal").modal('hide');
            return;
        }
        //需要增加判断合法性
        nametext=$("#itemname").val()
        if (trim(nametext).length==0){
            toastr.error('名称不能为空！', '输入错误');
            return
        }
 
        var itemdata = {
            'validate': getCookie('validation'), "id": selectItemID, "name": nametext,"orderno": $("#itemorderno").val(),
            "sleep": $("#itemsleep").val(), "openevent": $("#itemopenevent").val(),
            "closeevent": $("#itemcloseevent").val(),"desc": encodeURIComponent($("#itemdesc").val())
        }
        $.ajax({
            url: "/menuitems",
            type: selectItemID==-1? "PUT":"POST",
            data: itemdata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '更新节点';
                if (data.code == 0) {
                    if (data.itemid==selectItemID){
                    //更新记录
                    $('#menuItemsTable').bootstrapTable('updateByUniqueId', {
                        id: selectItemID, row: {
                            "NAME": $("#itemname").val(),
                            "ORDERNO": $("#itemorderno").val(),
                            "SLEEP": $("#itemsleep").val(), 
                            "OPENEVENT": $("#itemopenevent").val(),
                            "CLOSEEVENT": $("#itemcloseevent").val(),
                            "DESC": $("#itemdesc").val(),
                        }
                    });
                }
                else
                {
                    msg = '新增节点';
                    selectItemID=data.itemid
                    $('#menuItemsTable').bootstrapTable('append', 
                         {
                            "ID": selectItemID,
                            "ENABLE": 1,
                            "NAME": $("#itemname").val(),
                            "ORDERNO": $("#itemorderno").val(),
                            "SLEEP": $("#itemsleep").val(), 
                            "OPENEVENT": $("#itemopenevent").val(),
                            "CLOSEEVENT": $("#itemcloseevent").val(),
                            "DESC": $("#itemdesc").val(),
                        }
                    );

                }
                toastr.success(msg + '成功'); 
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '更新失败');
            }
        });
        //刷新记录
        // $('#menuItemsTable').bootstrapTable('refresh');
        $("#editModal").modal('hide');
    });
    //删除节点记录
    $('button#DELETE').on('click', function (e) {
        var itemsdata = { 'validate': getCookie('validation'), "id": selectItemID }
        $.ajax({
            url: '/menuitems',
            type: "DELETE",
            data: itemsdata,
            success: function (res) {
                var data = JSON.parse(res);
                msg = '删除节点';
                if (data.code == 0) {
                    //删除本地记录
                    $('#menuItemsTable').bootstrapTable('removeByUniqueId', selectItemID);
                    toastr.success(msg + '成功');
                } else {
                    toastr.error(data.message, msg + '失败');
                }
            },
            error: function () {
                toastr.error('服务器异常', '操作失败');
            }
        });
        //关闭窗体
        $("#deleteModal").modal('hide');
    });
});
