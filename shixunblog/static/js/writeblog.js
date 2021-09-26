var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        title: '',
        title_error: false,
        title_error_message: '文章标题格式错误',
        category: '0',
        category_error: false,
        category_error_message: '请选择文章分类',
        tags: '',
        tags_error: false,
        tags_error_message: '请输入标签',
        sumary: '',
        sumary_error: false,
        sumary_error_message: '请输入摘要内容',
        content: '',
        content_error: false,
        content_error_message: '请输入文章内容'
    },
    mounted() {

    },
    methods: {
        //检查文章标题
        check_title: function () {
            if (this.title.length <= 0 || this.title.length > 100) {
                this.title_error = true;
            } else {
                this.title_error = false;
            }
        },
        check_category: function () {
            if (this.category.length <= 0) {
                this.category_error = true;
            } else {
                this.category_error = false;
            }
        },
        check_tags: function () {
            if (this.tags.length <= 0) {
                this.tags_error = true;
            } else {
                this.tags_error = false;
            }
        },
        check_sumary: function () {
            if (this.sumary.length <= 0) {
                this.sumary_error = true;
            } else {
                this.sumary_error = false;
            }
        },
        check_content: function () {
            //获取 富文本框中的内容
            // 参考官方：https://ckeditor.com/docs/ckeditor4/latest/examples/api.html
            if (CKEDITOR.instances.id_body.getData().length <= 0) {
                this.content_error = true;
            } else {
                this.content_error = false;
            }
        },
        //提交
        on_submit: function () {
            this.check_title();
            this.check_category();
            this.check_tags();
            this.check_sumary();
            this.check_content();

            if (this.title_error == true || this.category_error == true || this.tags_error == true || this.sumary_error == true || this.content_error == true) {
                // 不满足登录条件：禁用表单
                window.event.returnValue = false;
            }
        }
    }
});
