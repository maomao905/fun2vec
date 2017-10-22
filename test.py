def test():
    print('start')
    while True:
        try:
            raise
        except Exception as e:
            print('exception')
            break
        finally:
            print('finally')

    print('end')

if __name__ == '__main__':
    test()
