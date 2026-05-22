<?php

// define("WEBMASTER_EMAIL", 'saidamirbobojonov@icloud.com');
$address = "saidamirbobojonov@icloud.com";
if (!defined("PHP_EOL")) define("PHP_EOL", "\r\n");

$error = false;
$fields = array('mail','phone','message' );

foreach ( $fields as $field ) {
	if ( empty($_POST[$field]) || trim($_POST[$field]) == '' )
		$error = true;
}

if ( !$error ) {

	$mail = stripslashes($_POST['mail']);	
	$phone = stripslashes($_POST['phone']);
	$message = stripslashes($_POST['message']);

	$e_subject = 'Portfolio contact from ' . $mail;
	

	// Configuration option.
	// You can change this if you feel that you need to.
	// Developers, you may wish to add more fields to the form, in which case you must be sure to add them here.

	$e_body = "You have been contacted by: $mail" . PHP_EOL . PHP_EOL;
	$e_phone = "\r\nPhone: $phone" . PHP_EOL . PHP_EOL;
	$e_message = "\r\nMessage: $message" . PHP_EOL . PHP_EOL;

	$msg = wordwrap( $e_body . $e_phone . $e_message , 70 );

	$headers = '';
	$headers .= "Mail: $mail" . PHP_EOL;
	$headers .= "Phone: $phone" . PHP_EOL;
	$headers .= "Message: $message" . PHP_EOL;
	// $headers .= "Content-type: text/plain; charset=utf-8" . PHP_EOL;
	// $headers .= "Content-Transfer-Encoding: quoted-printable" . PHP_EOL;

	if(mail($address, $e_subject, $msg, $headers  )) {

		// Email has sent successfully, echo a success page.
	
		echo 'Success';

	} else {

		echo 'ERROR!';

	}

}

?>
