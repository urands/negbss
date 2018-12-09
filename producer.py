import tkinter as tk
import tkinter
import pika



class TextExtension( tkinter.Frame ):
    """Extends Frame.  Intended as a container for a Text field.  Better related data handling
    and has Y scrollbar now."""


    def __init__( self, master, textvariable = None, *args, **kwargs ):
        self.textvariable = textvariable
        if ( textvariable is not None ):
            if not ( isinstance( textvariable, tkinter.Variable ) ):
                raise TypeError( "tkinter.Variable type expected, {} given.".format( type( textvariable ) ) )
            self.textvariable.get = self.GetText
            self.textvariable.set = self.SetText

        # build
        self.YScrollbar = None
        self.Text = None

        super().__init__( master )

        self.YScrollbar = tkinter.Scrollbar( self, orient = tkinter.VERTICAL )

        self.Text = tkinter.Text( self, yscrollcommand = self.YScrollbar.set, *args, **kwargs )
        self.YScrollbar.config( command = self.Text.yview )
        self.YScrollbar.pack( side = tkinter.RIGHT, fill = tkinter.Y )

        self.Text.pack( side = tkinter.LEFT, fill = tkinter.BOTH, expand = 1 )


    def Clear( self ):
        self.Text.delete( 1.0, tkinter.END )


    def GetText( self ):
        text = self.Text.get( 1.0, tkinter.END )
        if ( text is not None ):
            text = text.strip()
        if ( text == "" ):
            text = None
        return text


    def SetText( self, value ):
        self.Clear()
        if ( value is not None ):
            self.Text.insert( tkinter.END, value.strip() )

root =  tk.Tk()

#root.geometry("600x700") #You want the size of the app to be 500x500

text = TextExtension(root, font='Arial 10')

text.pack()

code=TextExtension(root,height=1, font='Arial 10',wrap=tk.WORD)

code.pack()


#hscrollbar.pack()
#vscrollbar.pack()

c = '''
#This is sample code for eval on consumer
def add(a,b):
    return a+b

''' 
text.SetText(c)

code.SetText( ' { "in" : [ 1, 1 ] , "call", "add" , "out", "return"  }')


clicks = 0

def click_button():
    global clicks, text
    clicks += 1
    root.title("Clicks {}".format(clicks))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    c = text.GetText()
    channel.exchange_declare(exchange='code',
                         exchange_type='fanout')
    channel.basic_publish(exchange='code',
                routing_key='',
                body=c
                )
    #print(c)
    channel.close()

def click_button_send():
    global clicks, text
    clicks += 1
    root.title("Clicks {}".format(clicks))
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    c = text.GetText()
    channel.basic_publish(exchange='',
                routing_key='bss',
                body=c
                )
    #print(c)
    channel.close()    



btn = tk.Button(text="Send code to all consumers", command=click_button)
btn.pack()

btn_msg = tk.Button(text="Send message", command=click_button_send)
#btn_msg.pack()


root.mainloop()

