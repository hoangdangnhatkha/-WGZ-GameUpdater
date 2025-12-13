const io = require("socket.io")(server);
const redis = require("redis"); // Dùng để lưu trạng thái tạm thời

io.on("connection", (socket) => {
  // 1. Khi người dùng đăng nhập
  socket.on("user_login", (userId) => {
    // Lưu socket.id gắn với userId để biết ai là ai
    saveUserSocket(userId, socket.id);

    // Cập nhật trạng thái trong Redis/DB
    setStatus(userId, "online");

    // Thông báo cho toàn bộ bạn bè hoặc server
    socket.broadcast.emit("user_status_change", {
      userId: userId,
      status: "online",
    });
  });

  // 2. Khi người dùng tắt app (Disconnect)
  socket.on("disconnect", () => {
    const userId = getUserIdFromSocket(socket.id);

    // Cập nhật trạng thái
    setStatus(userId, "offline");

    // Thông báo cho người khác
    socket.broadcast.emit("user_status_change", {
      userId: userId,
      status: "offline",
    });
  });
});
