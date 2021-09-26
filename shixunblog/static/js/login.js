var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        show_menu: false,
        mobile: '',
        password: '',
        remembered: '',
        mobile_error: false,
        mobile_error_message: '手机号错误',
        password: '',
        password_error: false,
        password_error_message: '密码错误',
    },
    mounted() {

    },
    methods: {
        //显示下拉菜单
        show_menu_click: function () {
            this.show_menu = !this.show_menu;
        },
        //检查手机号
        check_mobile: function () {
            var re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.mobile_error = false;
            } else {
                this.mobile_error = true;
            }
        },
        //检查密码
        check_password: function () {
            var re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)) {
                this.password_error = false;
            } else {
                this.password_error = true;
            }

        },
        //提交
        on_submit: function () {
            this.check_mobile();
            this.check_password();

            if (this.mobile_error == true || this.password_error == true) {
                // 不满足登录条件：禁用表单
                window.event.returnValue = false;
            }
        }
    }
});
