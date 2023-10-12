const express = require('express');
const bodyParser = require('body-parser');

const app = express();

// 仮のユーザーデータベース
const users = [
    { email: 'test@example.com', password: 'password123' }
];

app.use(bodyParser.urlencoded({ extended: false }));

app.post('/login', (req, res) => {
    const { email, password } = req.body;

    const user = users.find(u => u.email === email && u.password === password);

    if (user) {
        res.send('ログイン成功！');
    } else {
        res.send('メールアドレスまたはパスワードが間違っています。');
    }
});

app.listen(3000, () => {
    console.log('Server is running on http://localhost:3000');
});
