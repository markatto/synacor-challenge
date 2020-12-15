6027    JT      r0      6035 			# if r0 != 0
6030    ADD     r0      r1      1		#   r0 = r1 + 1
6034    RET					#   return
6035    JT      r1      6048			# else if r1 != 0
6038    ADD     r0      r0      32767		#   r0 -= 1
6042    SET     r1      r7			#   r1 = r7
6045    CALL    6027				#   recurse()
6047    RET					#   return
						# else
6048    PUSH    r0				#   push r0
6050    ADD     r1      r1      32767		#   r1 -= 1
6054    CALL    6027				#   recurse()

6056    SET     r1      r0			# r1 = r0
6059    POP     r0
6061    ADD     r0      r0      32767		# r0 -= 1
6065    CALL    6027
6067    RET
