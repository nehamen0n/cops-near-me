$(document).ready(function () {
  $("#phonenum").click(function () {
    $("#error").empty();
    let unum = $("#unum").val();
    console.log(unum);
    if (!isNaN(unum) && unum.length === 10) {
      console.log("working");
      $.ajax({
        type: "POST",
        url: "login",
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({ phonenumber: unum }),
        success: function () {
          console.log("sucess");
          window.location.href = "/userlocation";
        },
        error: function (request, status, error) {
          console.log("Error");
          console.log(request);
          console.log(status);
          console.log(error);
        },
      });
    } else {
      console.log("brokem");
      $("#unum").focus();
      $("#error").append("This is not a valid number. Please try again");
    }
  });
});
